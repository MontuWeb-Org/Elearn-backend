#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# ONE-TIME BOOTSTRAP. This generated the 23 pages in docs/api/reference/ from
# the tags in docs/api/openapi.yaml.
#
# Those pages are now edited by hand. RE-RUNNING THIS OVERWRITES THEM.
# Useful only if you add a whole new tag and want the page scaffolded.
# ---------------------------------------------------------------------------
import yaml, collections, os
BASE="/home/elhussienawad/Montu/Elearn-backend/docs/api"
SRC="https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml"
spec=yaml.safe_load(open(f"{BASE}/openapi.yaml"))

# tag -> [(path, method, op)] preserving spec order
bytag=collections.OrderedDict()
for p,ms in spec["paths"].items():
    for m,o in ms.items():
        bytag.setdefault(o["tags"][0],[]).append((p,m,o))

def hint(style,body): return f"{{% hint style=\"{style}\" %}}\n{body}\n{{% endhint %}}\n"

def block(path,method):
    return (f'{{% openapi src="{SRC}" path="{path}" method="{method}" %}}\n'
            f'{SRC}\n{{% endopenapi %}}\n')

def counts(items):
    c=collections.Counter()
    for _,_,o in items:
        d=o["description"]
        c["blocked" if "🚫" in d else "decision" if "⚠️" in d else "ready"]+=1
    return c

# per-tag intro prose and target filename
PAGES = {
"Authentication": ("authentication","Authentication",
 "One login serves all four tiers. The server resolves the caller's role and returns a "
 "`routing_target`; the client does not decide where to land.\n\n"
 "Authentication is an access token plus a refresh token. The refresh token is stored hashed in "
 "`USER_SESSIONS` and **rotates on every use** — presenting an old one revokes the session. "
 "\"Remember me\" on WF 01 affects refresh-token lifetime only; it does not change the access "
 "token.\n\n"
 "**Only instructors self-register.** TA, student and parent accounts are always created by an "
 "instructor-issued invite — see [Invites](invites.md)."),
"Invites": ("invites","Invites",
 "Every non-instructor account in the platform arrives through an invite. The instructor issues "
 "one, the recipient opens a public preview showing exactly what access they are being granted, "
 "and accepting creates the account with that scope already applied.\n\n"
 "The scope is role-shaped. An assistant invite carries group ids and the three permission flags; "
 "a parent invite carries the `student_id` to link, and the link is auto-approved on acceptance — "
 "there is no pending or rejected state."),
"Billing": ("billing","Billing",
 "Instructor → platform subscriptions. **This is not student fees** — that is a separate money "
 "flow with separate entities, documented under [Fees](fees.md). Confusing the two is the most "
 "common misreading of the schema."),
"Courses": ("courses","Courses",
 "The root of the curriculum branch. A course belongs to one instructor and fans out two ways: "
 "into chapters and lessons (the syllabus, authored once) and into groups (the sections that "
 "actually take it). See [The two branches](../concepts/two-branches.md).\n\n"
 "\"Term\" is not an entity. `IG Physics — Term 1` is one course; a second term is a second "
 "course."),
"Chapters": ("chapters","Chapters",
 "Chapters order the syllabus within a course. The Curriculum Builder loads its whole tree from "
 "`GET /courses/{courseId}/chapters?include=lessons` — one request per page load.\n\n"
 "**Reordering is a collection-level `PUT`, not a `PATCH` per item.** `UNIQUE (course_id, "
 "order_index)` means moving chapters one at a time collides mid-sequence, so a drag-and-drop "
 "sends the complete ordered array and the server reassigns every index in one transaction. "
 "Lessons, recordings, assignments and quiz questions all follow the same pattern."),
"Lessons": ("lessons","Lessons",
 "A lesson hangs off a **chapter**, not a course — `LESSONS.chapter_id` is the foreign key and the "
 "course is derived through it.\n\n"
 "Deleting a lesson cascades to its materials and recordings, but **never destroys attendance "
 "history**: `LIVE_SESSIONS.lesson_id` is `SET NULL`, so a class that covered the lesson survives "
 "with its attendance intact. `QUIZZES.lesson_id` behaves the same way. The delete does fail if "
 "any of the lesson's assignments has submissions."),
"Materials": ("materials","Materials",
 "Files attached to a lesson — the feature that replaces emailing PDFs one by one.\n\n"
 "Materials are curriculum: authored once against a lesson and identical for every group taking "
 "the course. They are never nested under a group."),
"Recordings": ("recordings","Recordings",
 "On-demand video attached to a lesson. Most recordings are pre-authored content, but one may "
 "point back at the live class it is a replay of — at most one recording per class, enforced by "
 "`UNIQUE (recorded_from_live_session_id)`."),
"Uploads": ("uploads","Uploads",
 "Files live in external storage; the database holds URLs only. Upload transport is deliberately "
 "separate from the resource APIs: request a signed target here, `PUT` the bytes directly to it, "
 "then pass the returned `file_url` to whichever create call needs it."),
"Assignments": ("assignments","Assignments",
 "Homework. **Assignments are not quizzes**, and the two are separate entities on separate "
 "branches — see [The two branches](../concepts/two-branches.md).\n\n"
 "An assignment attaches to a **lesson**, is authored once, and is seen by every group taking the "
 "course. It is checked for on-time submission and **never scored**. The feedback mechanism is a "
 "solution file, released after the deadline, that the student self-checks against.\n\n"
 "The three states the roster shows are derived, not stored: **Submitted** is a row with "
 "`is_late = false`, **Late** is a row with `is_late = true`, and **Missing** is the absence of a "
 "row once the deadline has passed."),
"Groups": ("groups","Groups",
 "A group is a cohort — what the wireframes call a **section**. \"Section A\", \"Section B\" and "
 "\"Revision\" are three groups of one course.\n\n"
 "`schedule_info` and `classroom_location` on a group are **defaults, not truth**. They describe "
 "the usual pattern (\"Sun/Tue 4pm, Room B\"); the authoritative time and place for any given "
 "class live on the [live session](scheduling.md) row, which is free to differ for a makeup or a "
 "relocated class.\n\n"
 "**There is no group delete.** A cohort with history cannot be removed — archive it."),
"Assistants": ("assistants","Assistants",
 "Teaching assistants hold delegated, scoped access. Two independent axes control what a TA can "
 "do, and both live on `GROUP_ASSISTANTS`:\n\n"
 "- **Scope** — which groups. One row per group; \"All sections\" is N rows, not a wildcard, so a "
 "TA does *not* automatically inherit access to sections created later.\n"
 "- **Permissions** — three booleans matching the invite-time checkboxes exactly: "
 "`can_take_attendance`, `can_grade`, `can_upload_solutions`.\n\n"
 "**Revoking a TA is never a row delete.** Grading history points at the user, so revocation sets "
 "`is_revoked` — access ends immediately while every grade they gave keeps its attribution."),
"Scheduling": ("scheduling","Scheduling",
 "One calendar for physical center classes and virtual sessions alike. A live session is one "
 "scheduled class with its own time and room, and it is the **only** thing attendance records "
 "against.\n\n"
 "`mode` drives two validation rules: `ONLINE` requires a `meeting_url`, `ONSITE` requires a "
 "`classroom_location`. `lesson_id` is nullable on purpose — revision, exam prep and open Q&A are "
 "real classes that map to no single lesson."),
"Attendance": ("attendance","Attendance",
 "Attendance records against a **live session**, never against a lesson, a course or a day.\n\n"
 "Saving is a single bulk `PUT` carrying the full status array. That one endpoint serves both "
 "\"Mark all present\" and \"Save Attendance\" — at 150+ students, one request per student is the "
 "wrong shape."),
"Quizzes": ("quizzes","Quizzes",
 "Timed assessments on the **cohort branch**: issued to one group, with an availability window and "
 "a per-attempt clock.\n\n"
 "`opens_at` and `closes_at` bound when the quiz is available; `duration_seconds` is the clock "
 "that starts when a student begins. A quiz may be open for a week but allow 30 minutes once "
 "started — either bound may bind first. Omit the duration for an untimed quiz.\n\n"
 "`lesson_id` on a quiz is **tagging only**. It does not move the quiz onto the curriculum branch, "
 "and it must belong to the group's own course."),
"Quiz attempts": ("attempts","Quiz attempts",
 "The student side. An attempt *is* the record — there is no separate submission entity.\n\n"
 "Starting an attempt materializes `expires_at` as `min(started_at + duration, quiz.closes_at)`. "
 "Storing it rather than recomputing it on every read is deliberate: the countdown, the "
 "auto-submit and late-answer rejection then all read one authoritative instant instead of three "
 "computations that can disagree.\n\n"
 "On submit, MCQs auto-score into `auto_score` immediately; `total_score` stays null until a "
 "human has graded every structured answer. That split is what makes \"MCQ score shows "
 "immediately, overall grade stays pending\" representable."),
"Grading": ("grading","Grading",
 "The teaching assistant's queue, and the whole of wireframe 15.\n\n"
 "Two facts shape every endpoint here:\n\n"
 "**The queue is a query, not a table.** Pending work is `QUIZ_ANSWERS` where `points_awarded IS "
 "NULL`, joined to `QUIZ_QUESTIONS` on `question_type = 'STRUCTURED'` and to `GROUP_ASSISTANTS` "
 "for scope. A partial index exists for exactly this shape.\n\n"
 "**The unit of work is one answer, not one attempt.** The queue serves \"Youssef T. — Q4 "
 "(structured answer)\" with its own score box. Two assistants may legitimately grade different "
 "questions of the same student's paper, which is why grader attribution lives on the answer and "
 "not only on the attempt.\n\n"
 "MCQs never appear here — they are auto-scored at submit. A null `graded_by_user_id` on a scored "
 "answer means the machine graded it, not that attribution is missing.\n\n"
 "**Assignments have no grading queue.** They are checked for on-time submission and self-checked "
 "against a released solution. The only homework action on this screen is uploading that "
 "solution, which needs `can_upload_solutions`, not `can_grade`."),
"Roster": ("roster","Roster",
 "Who is keeping up and who is not, across 150+ students and multiple sections. Every aggregate "
 "on these endpoints — attendance percentage, average grade, homework state — is **computed on "
 "read and never stored**."),
"Dashboards": ("dashboards","Dashboards",
 "One landing endpoint per role. All four are pure aggregate reads with no writes, and every "
 "number they return is derived."),
"Fees": ("fees","Fees",
 "Student → instructor payments. **Distinct from [Billing](billing.md)**, which is the instructor's "
 "own subscription to the platform. Two different money flows, two different entity sets."),
"Parent portal": ("parents","Parent portal",
 "Parents monitor; they never edit. Two invariants govern every endpoint in this group:\n\n"
 "1. **A parent reads nothing outside their linked children.** Every query is filtered by the "
 "caller's `PARENT_STUDENTS` rows. No parent-visible endpoint accepts a `student_id` without that "
 "check.\n"
 "2. **A parent is read-only on academic records.** Attendance, grades and schedule are never "
 "writable by a parent. The single parent write in the entire API is fee payment.\n\n"
 "The parent–child link is many-to-many in both directions: one parent follows several children, "
 "and one child may be followed by both parents. It is deliberately **not** scoped to an "
 "instructor — a parent with children under two instructors holds one account and one set of "
 "links."),
"Notifications": ("notifications","Notifications",
 "The persisted in-app feed. Delivery is in-app only; email and push are out of scope for this "
 "version."),
"Events": (None,None,None),
"Student portal": ("student","Student portal",
 "Students never browse courses directly. They reach curriculum **through** a group enrollment, "
 "which is why every read here is scoped under `/me` rather than under `/courses`.\n\n"
 "Only published lessons are visible. Drafts are invisible to students and parents alike."),
}

os.makedirs(f"{BASE}/reference",exist_ok=True)
written=[]
# within a page, the tag's own path prefix leads; borrowed paths follow
LEAD={"Grading":"/grading","Quiz attempts":"/quizzes","Assistants":"/assistants",
      "Chapters":"/courses","Lessons":"/chapters","Assignments":"/lessons"}
for tag,items in bytag.items():
    if tag=="Events": continue
    if tag in LEAD:
        pref=LEAD[tag]
        items=sorted(enumerate(items),key=lambda t:(not t[1][0].startswith(pref),t[0]))
        items=[i for _,i in items]
    slug,title,intro=PAGES[tag]
    c=counts(items)
    parts=[f"# {title}\n",intro+"\n"]
    bits=[]
    if c["ready"]:    bits.append(f"**{c['ready']} ready**")
    if c["decision"]: bits.append(f"**{c['decision']}** awaiting a decision")
    if c["blocked"]:  bits.append(f"**{c['blocked']} blocked**")
    parts.append(hint("info",
      f"{len(items)} operations — {', '.join(bits)}. Each operation states its own status; see "
      f"[Specification status](../concepts/status.md) for what the labels mean."))
    for p,m,o in items:
        parts.append(f"\n## {o['summary']}\n")
        parts.append(block(p,m))
    open(f"{BASE}/reference/{slug}.md","w").write("\n".join(parts))
    written.append(slug)
print("reference pages:",len(written))
