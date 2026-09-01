#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# ONE-TIME BOOTSTRAP. This generated the first version of docs/api/openapi.yaml
# from docs/api-resource-map.md.
#
# docs/api/openapi.yaml is now the source of truth and is edited by hand.
# RE-RUNNING THIS OVERWRITES EVERY HAND EDIT. It is kept for reference only —
# to see how the initial spec was derived from the ERD and the wireframes.
#
#   Regenerate (destructive):  python3 scripts/bootstrap-openapi.py
#   Validate instead:          npm run docs:lint
# ---------------------------------------------------------------------------
import yaml, collections

paths = collections.OrderedDict()

def op(tag, opid, summary, desc, roles, scope, wf, status,
       params=None, body=None, ok=None, ok_code="200", errors=None, public=False):
    d = f"{desc}\n\n**Roles:** {roles}  \n**Ownership scope:** {scope}  \n**Wireframe:** {wf}\n\n{status}"
    o = {"tags": [tag], "operationId": opid, "summary": summary, "description": d}
    if public: o["security"] = []
    if params: o["parameters"] = params
    if body: o["requestBody"] = {"required": True,
        "content": {"application/json": {"schema": body}}}
    r = {ok_code: {"description": "Success", "content":
         {"application/json": {"schema": ok or {"$ref": "#/components/schemas/Empty"}}}}}
    if ok_code == "204": r = {"204": {"description": "No content"}}
    for e in (errors or []): r[e] = {"$ref": f"#/components/responses/{e}"}
    for e in ("401", "403"):
        if not public and e not in r: r[e] = {"$ref": f"#/components/responses/{e}"}
    o["responses"] = r
    return o

def add(path, method, operation):
    paths.setdefault(path, {})[method] = operation

def P(name, desc, where="path", schema=None, required=None):
    return {"name": name, "in": where, "required": required if required is not None else (where=="path"),
            "description": desc, "schema": schema or {"type": "string", "format": "uuid"}}

def ref(n):  return {"$ref": f"#/components/schemas/{n}"}
def arr(n):  return {"type": "array", "items": ref(n)}
def page(n): return {"allOf": [ref("PageEnvelope"),
    {"type": "object", "properties": {"data": arr(n)}}]}

OK   = "**Status:** ✅ Specifiable — fully backed by the ERD."
def WARN(t): return f"**Status:** ⚠️ {t}"
def BLOCK(t): return f"**Status:** 🚫 Blocked — {t} The shape below is proposed, not final."

LIMIT  = P("limit", "Page size (default 25, max 100).", "query", {"type":"integer","default":25,"maximum":100}, False)
CURSOR = P("cursor", "Opaque cursor from a previous response's `page.next_cursor`.", "query", {"type":"string"}, False)

# ============================ AUTH & IDENTITY ============================
T="Authentication"
add("/auth/login","post",op(T,"login","Log in",
 "Exchanges credentials for an access token and a refresh token. The response carries the "
 "caller's roles and a `routing_target`, because one login serves all four tiers and the server "
 "decides where the client lands (WF 01).",
 "—","—","01",OK,body=ref("LoginRequest"),ok=ref("AuthSession"),errors=["400","401"],public=True))
add("/auth/refresh","post",op(T,"refreshToken","Rotate refresh token",
 "Exchanges a refresh token for a new pair. The old token is revoked on use — rotation is "
 "backed by `USER_SESSIONS.refresh_token_hash`.",
 "—","—","—",OK,body=ref("RefreshRequest"),ok=ref("AuthSession"),errors=["401"],public=True))
add("/auth/logout","post",op(T,"logout","Log out",
 "Revokes the current session by setting `USER_SESSIONS.is_revoked`.",
 "all","self","—",OK,ok_code="204"))
add("/auth/me","get",op(T,"getCurrentUser","Current user",
 "The caller's profile, roles and routing target.","all","self","all",OK,ok=ref("CurrentUser")))
add("/auth/register","post",op(T,"registerInstructor","Register as instructor",
 "Step 1 of 3 of instructor sign-up. Creates the `USERS` row, the `TEACHERS` profile and the "
 "`TEACHER` role assignment. Only instructors may self-register; every other account arrives by invite.",
 "—","—","02",
 WARN("WF 02 captures a single `full_name`, plural `subjects_taught` and a curriculum choice "
      "(IGCSE / American Diploma / Both). `USERS` splits `first_name`/`last_name`, `TEACHERS."
      "specialization` is one string, and no curriculum field exists anywhere (gaps A21, G16). "
      "The three fields below are documented against the wireframe and await a schema change."),
 body=ref("RegisterRequest"),ok=ref("AuthSession"),errors=["400","409"],public=True))
add("/auth/password/forgot","post",op(T,"forgotPassword","Request a password reset",
 "Sends a reset link. **Always returns 202**, whether or not the address matches an account — "
 "leaking account existence is the failure mode here (WF 03).",
 "—","—","03",BLOCK("no `PASSWORD_RESET_TOKENS` entity exists (G5)."),
 body=ref("ForgotPasswordRequest"),ok_code="202",public=True))
add("/auth/password/reset","post",op(T,"resetPassword","Reset a password",
 "Consumes a reset token and sets a new password. Expired links offer a resend (WF 03).",
 "—","—","03",BLOCK("no `PASSWORD_RESET_TOKENS` entity exists (G5)."),
 body=ref("ResetPasswordRequest"),ok_code="204",errors=["400"],public=True))
add("/me/profile","get",op(T,"getProfile","Get own profile",
 "Profile tab on WF 13 (instructor) and WF 19 (student).","all","self","13, 19",
 WARN("No avatar or display-name field exists on `USERS` (gap A25), and no student-editable "
      "profile fields are defined (A26)."),ok=ref("Profile")))
add("/me/profile","patch",op(T,"updateProfile","Update own profile",
 "Partial update. Only fields present in the body are changed.","all","self","13, 19",
 WARN("See `GET /me/profile`."),body=ref("ProfileUpdate"),ok=ref("Profile"),errors=["400"]))
add("/me/sessions","get",op(T,"listSessions","List active devices",
 "Active refresh-token sessions with user agent and IP.","all","self","—",
 WARN("`USER_SESSIONS` stores `user_agent`, `ip_address`, `is_revoked` and `expires_at`, but no "
      "screen lists or revokes sessions (gap B3). Documented because the data exists."),
 ok=page("UserSession"),params=[LIMIT,CURSOR]))
add("/me/sessions/{sessionId}","delete",op(T,"revokeSession","Revoke a device",
 "Sets `is_revoked` on one session.","all","self","—",WARN("See `GET /me/sessions`."),
 params=[P("sessionId","The session to revoke.")],ok_code="204",errors=["404"]))

# ============================ INVITES ============================
T="Invites"
IB = BLOCK("no `INVITES` entity exists (G4). Every non-instructor account arrives this way, so "
           "this is the highest-priority gap in the schema.")
add("/invites","post",op(T,"createInvite","Issue an invite",
 "Creates an invite for a TA, student or parent. `scope` is role-shaped: for `ASSISTANT` it carries "
 "the group ids plus the three permission flags; for `PARENT` it carries the `student_id` to link. "
 "Accepting a `PARENT` invite writes the `PARENT_STUDENTS` row and is auto-approved — there is no "
 "pending state (WF 05).","I","own-course","13, 05",IB,
 body=ref("InviteCreate"),ok=ref("Invite"),ok_code="201",errors=["400","409"]))
add("/invites","get",op(T,"listInvites","List pending invites",
 "Invites issued by the caller that have not yet been accepted.","I","own-course","13",IB,
 ok=page("Invite"),params=[P("role","Filter by invited role.","query",ref("RoleName"),False),LIMIT,CURSOR]))
add("/invites/{inviteId}","delete",op(T,"revokeInvite","Rescind an invite",
 "Invalidates a pending invite token.","I","own-course","13",IB,
 params=[P("inviteId","The invite to rescind.")],ok_code="204",errors=["404"]))
add("/invite-tokens/{token}","get",op(T,"previewInvite","Preview an invite",
 "**Public.** Returns the inviter's name, the offered role, and the scope rendered as prose — WF 04 "
 "shows the TA their boundaries (\"attendance, grading, and homework uploads\") before they activate.",
 "—","—","04, 05",IB,
 params=[P("token","The invite token from the emailed link.",schema={"type":"string"})],
 ok=ref("InvitePreview"),errors=["404","410"],public=True))
add("/invite-tokens/{token}/accept","post",op(T,"acceptInvite","Accept an invite",
 "Creates the account, applies the invite's scope, and returns tokens plus the routing target.",
 "—","—","04, 05",IB,
 params=[P("token","The invite token.",schema={"type":"string"})],
 body=ref("InviteAccept"),ok=ref("AuthSession"),errors=["400","410"],public=True))

# ============================ BILLING ============================
T="Billing"
add("/plans","get",op(T,"listPlans","List subscription plans",
 "Plan tiers for sign-up step 2.","—","—","02",
 WARN("WF 02 sizes the plan on student count **and TA seats**, but `SUBSCRIPTION_PLANS` has only "
      "`max_students` — whether TAs consume seats is undecided (gap D20)."),
 ok=arr("Plan"),public=True))
add("/subscriptions","post",op(T,"createSubscription","Subscribe to a plan",
 "Sign-up step 3. Payment processing is delegated to a provider; this endpoint takes the "
 "provider's token and records the `SUBSCRIPTIONS` row.","I","self","02",
 WARN("Payment provider integration is out of scope for this document."),
 body=ref("SubscriptionCreate"),ok=ref("Subscription"),ok_code="201",errors=["400","422"]))
add("/me/subscription","get",op(T,"getSubscription","Get own subscription",
 "Billing tab on WF 13.","I","self","13",OK,ok=ref("Subscription")))
add("/me/subscription","patch",op(T,"updateSubscription","Change or cancel plan",
 "Switches plan or sets `status = CANCELLED`.","I","self","13",
 WARN("No screen edits plan limits or subscription state (gap B2)."),
 body=ref("SubscriptionUpdate"),ok=ref("Subscription"),errors=["400","422"]))

# ============================ CURRICULUM ============================
T="Courses"
CID = P("courseId","The course.")
add("/courses","get",op(T,"listCourses","List courses",
 "The instructor's courses. A TA sees courses of groups they are assigned to.","I, A",
 "own-course / assigned-group","06, 07",OK,
 params=[P("status","Filter by lifecycle status.","query",ref("CourseStatus"),False),LIMIT,CURSOR],
 ok=page("Course")))
add("/courses","post",op(T,"createCourse","Create a course",
 "New courses start as `DRAFT`.","I","self","02, 07",OK,
 body=ref("CourseCreate"),ok=ref("Course"),ok_code="201",errors=["400","409"]))
add("/courses/{courseId}","get",op(T,"getCourse","Get a course",
 "Course header — WF 07's \"IG Physics — Term 1\".","I, A","own-course","07",
 WARN("\"Term\" has no entity. A term is folded into the course, i.e. one course per term "
      "(gap G14). Confirm before building."),params=[CID],ok=ref("Course"),errors=["404"]))
add("/courses/{courseId}","patch",op(T,"updateCourse","Update a course",
 "Rename, edit description, or change `status`.","I","own-course","07",OK,
 params=[CID],body=ref("CourseUpdate"),ok=ref("Course"),errors=["400","404"]))
add("/courses/{courseId}","delete",op(T,"deleteCourse","Delete a course",
 "Cascades the whole curriculum spine: chapters, lessons, materials, recordings and assignments. "
 "Fails if any assignment has submissions.","I","own-course","—",
 WARN("No screen offers this, and deletion-versus-archival is undecided (gap D26). Documented "
      "because the cascade rules define it."),
 params=[CID],ok_code="204",errors=["404","409"]))
add("/courses/{courseId}/chapters","get",op("Chapters","listChapters","List chapters",
 "Chapters in `order_index` order. Pass `include=lessons` to nest each chapter's lessons — this is "
 "**the Curriculum Builder's page-load read** (WF 07), and it replaces the separate `/tree` endpoint "
 "that earlier drafts proposed.","I, A","own-course","07",OK,
 params=[CID,P("include","Set to `lessons` to nest lessons inside each chapter.","query",
   {"type":"string","enum":["lessons"]},False)],ok=page("Chapter")))
add("/courses/{courseId}/chapters","post",op("Chapters","createChapter","Create a chapter",
 "\"+ Add Chapter\". `order_index` appends to the end when omitted.","I","own-course","07",OK,
 params=[CID],body=ref("ChapterCreate"),ok=ref("Chapter"),ok_code="201",errors=["400","409"]))
add("/courses/{courseId}/chapters/order","put",op("Chapters","reorderChapters","Reorder chapters",
 "**Bulk.** The body is the complete ordered array of chapter ids; the server reassigns every "
 "`order_index` in one transaction.\n\nThis is a collection-level `PUT` rather than a `PATCH` per "
 "chapter because `UNIQUE (course_id, order_index)` makes naive per-item reordering collide "
 "mid-sequence. One drag-and-drop is one request.","I","own-course","07",OK,
 params=[CID],body=ref("ReorderRequest"),ok=arr("Chapter"),errors=["400","409"]))
T="Chapters"
CHID = P("chapterId","The chapter.")
add("/chapters/{chapterId}","get",op(T,"getChapter","Get a chapter","Single chapter.",
 "I, A","own-course","07",OK,params=[CHID],ok=ref("Chapter"),errors=["404"]))
add("/chapters/{chapterId}","patch",op(T,"updateChapter","Update a chapter",
 "\"Edit\" on WF 07 — title and description.","I","own-course","07",OK,
 params=[CHID],body=ref("ChapterUpdate"),ok=ref("Chapter"),errors=["400","404"]))
add("/chapters/{chapterId}","delete",op(T,"deleteChapter","Delete a chapter",
 "Cascades to lessons, and through them to materials, recordings and assignments.",
 "I","own-course","07",OK,params=[CHID],ok_code="204",errors=["404","409"]))
add("/chapters/{chapterId}/lessons","get",op("Lessons","listLessons","List lessons",
 "Lessons in `order_index` order.","I, A","own-course","07",OK,params=[CHID],ok=page("Lesson")))
add("/chapters/{chapterId}/lessons","post",op("Lessons","createLesson","Create a lesson",
 "\"+ Add Lesson\".\n\nNote the parent: a lesson hangs off a **chapter**, not a course. `LESSONS."
 "chapter_id` is the foreign key and the course is derived through it.","I","own-course","07",OK,
 params=[CHID],body=ref("LessonCreate"),ok=ref("Lesson"),ok_code="201",errors=["400","409"]))
add("/chapters/{chapterId}/lessons/order","put",op("Lessons","reorderLessons","Reorder lessons",
 "**Bulk**, same contract as chapter reordering.","I","own-course","07",OK,
 params=[CHID],body=ref("ReorderRequest"),ok=arr("Lesson"),errors=["400","409"]))
T="Lessons"
LID = P("lessonId","The lesson.")
add("/lessons/{lessonId}","get",op(T,"getLesson","Get a lesson",
 "Lesson header for the Content & Assessment Hub.","I, A","own-course","08",OK,
 params=[LID],ok=ref("Lesson"),errors=["404"]))
add("/lessons/{lessonId}","patch",op(T,"updateLesson","Update a lesson","Title and description.",
 "I","own-course","07, 08",OK,params=[LID],body=ref("LessonUpdate"),ok=ref("Lesson"),errors=["400","404"]))
add("/lessons/{lessonId}","delete",op(T,"deleteLesson","Delete a lesson",
 "Cascades to the lesson's materials and recordings.\n\n**Attendance history is never destroyed.** "
 "`LIVE_SESSIONS.lesson_id` is `SET NULL`, so a class that covered this lesson survives with its "
 "attendance intact and its lesson link cleared. `QUIZZES.lesson_id` is `SET NULL` for the same reason. "
 "The delete fails if any of the lesson's assignments has submissions.",
 "I","own-course","07",OK,params=[LID],ok_code="204",errors=["404","409"]))
add("/lessons/{lessonId}/publish","post",op(T,"publishLesson","Publish a lesson",
 "Draft → Published. Makes the lesson and its attached materials and recordings visible on the "
 "student's Lesson view (WF 20). Modelled as a state transition rather than a `PATCH` field so the "
 "real-time fan-out has a single hook.","I","own-course","07",
 BLOCK("`LESSONS` has no `status` field (G3). Whether a published material inside a draft lesson is "
       "visible is also undecided (gap D2)."),params=[LID],ok=ref("Lesson"),errors=["404"]))
add("/lessons/{lessonId}/unpublish","post",op(T,"unpublishLesson","Unpublish a lesson",
 "Published → Draft. Drafts are invisible to students and parents.","I","own-course","07",
 BLOCK("`LESSONS` has no `status` field (G3)."),params=[LID],ok=ref("Lesson"),errors=["404"]))

# ============================ MATERIALS & RECORDINGS ============================
T="Materials"
MID = P("materialId","The material.")
G7 = BLOCK("`MATERIALS` has no `access_mode`, `size_bytes` or `mime_type` (gaps G7, A9). WF 08 shows "
           "\"1.2 MB\" and a type icon and sets view-only vs downloadable at upload.")
add("/lessons/{lessonId}/materials","get",op(T,"listMaterials","List materials",
 "Files attached to a lesson. Students see them only for published lessons.",
 "I, A, S","own-course / own-enrollment","08, 20",
 WARN("`size_bytes` and `mime_type` are not stored, so the WF 08 file-size label and type icon "
      "have no source (gaps A9, C11)."),params=[LID],ok=page("Material")))
add("/lessons/{lessonId}/materials","post",op(T,"createMaterial","Attach a material",
 "Registers a file already uploaded via `POST /uploads`. `access_mode` decides whether students may "
 "download it or only stream it.","I, A","own-course / assigned-group + can_upload_solutions","08",G7,
 params=[LID],body=ref("MaterialCreate"),ok=ref("Material"),ok_code="201",errors=["400"]))
add("/materials/{materialId}","patch",op(T,"updateMaterial","Update a material",
 "Rename, or change the access mode.","I","own-course","08",G7,
 params=[MID],body=ref("MaterialUpdate"),ok=ref("Material"),errors=["400","404"]))
add("/materials/{materialId}","delete",op(T,"deleteMaterial","Delete a material",
 "Removes the record. Deleting the underlying blob is a storage concern.","I","own-course","08",OK,
 params=[MID],ok_code="204",errors=["404"]))
add("/materials/{materialId}/content","get",op(T,"getMaterialContent","Get a download URL",
 "Issues a short-lived signed URL honouring the material's `access_mode`.",
 "I, A, S, P","own-course / own-enrollment / linked-child","20",
 BLOCK("`access_mode` does not exist (G7), and how view-only is enforced — streamed, signed URL, or "
       "DRM — is undecided (gap D21)."),params=[MID],ok=ref("SignedUrl"),errors=["404"]))
add("/materials/{materialId}/views","post",op(T,"logMaterialView","Log a material view",
 "Records that the student opened the file. WF 20 promises this \"viewed\" state is visible to the "
 "instructor on the roster (WF 11).","S","own-enrollment","20",
 BLOCK("no `MATERIAL_VIEWS` table exists (G8). The ERD names it as the natural extension."),
 params=[MID],ok_code="204",errors=["404"]))
T="Recordings"
RID = P("recordingId","The recording.")
RW = WARN("`publish_at`, `deadline` and `max_watch_limit` are **declarative and unenforced in this "
          "pass** — the ERD says so explicitly. The fields accept values; the platform does not yet "
          "police them. Enforcement needs the view log from G8.")
add("/lessons/{lessonId}/recordings","get",op(T,"listRecordings","List recordings",
 "On-demand video for a lesson, in `order_index` order.","I, A, S",
 "own-course / own-enrollment","08, 20",OK,params=[LID],ok=page("Recording")))
add("/lessons/{lessonId}/recordings","post",op(T,"createRecording","Add a recording",
 "Registers a video. `recorded_from_live_session_id` may point back at the live class this is a "
 "replay of — at most one recording per class.","I","own-course","08",RW,
 params=[LID],body=ref("RecordingCreate"),ok=ref("Recording"),ok_code="201",errors=["400","409","422"]))
add("/recordings/{recordingId}","patch",op(T,"updateRecording","Update a recording",
 "Edit the title or the gating fields.","I","own-course","08",RW,
 params=[RID],body=ref("RecordingUpdate"),ok=ref("Recording"),errors=["400","404","422"]))
add("/recordings/{recordingId}","delete",op(T,"deleteRecording","Delete a recording","Removes the record.",
 "I","own-course","08",OK,params=[RID],ok_code="204",errors=["404"]))
add("/lessons/{lessonId}/recordings/order","put",op(T,"reorderRecordings","Reorder recordings",
 "**Bulk**, same contract as chapters and lessons.","I","own-course","08",OK,
 params=[LID],body=ref("ReorderRequest"),ok=arr("Recording"),errors=["400","409"]))
add("/recordings/{recordingId}/views","post",op(T,"logRecordingView","Log a recording view",
 "Increments the student's watch count — the basis for enforcing `max_watch_limit`.",
 "S","own-enrollment","20",BLOCK("no `RECORDED_SESSION_VIEWS` table exists (G8)."),
 params=[RID],ok_code="204",errors=["404"]))
add("/uploads","post",op("Uploads","createUpload","Request an upload target",
 "Returns a short-lived signed `PUT` URL and the `file_url` to pass to whichever resource create "
 "call needs it — material, recording, assignment solution, or homework submission.\n\nFiles are "
 "stored externally; the ERD holds URLs only. Upload transport is deliberately separate from the "
 "resource APIs.","I, A, S","self","08, 15, 23",
 WARN("Storage provider is not chosen. Size and MIME limits are unspecified."),
 body=ref("UploadRequest"),ok=ref("UploadTarget"),ok_code="201",errors=["400","422"]))

# ============================ ASSIGNMENTS ============================
T="Assignments"
AID = P("assignmentId","The assignment.")
OQ1 = WARN("`ASSIGNMENTS.due_date` is a single absolute timestamp on a **cohort-independent** row, so "
           "every section of the course shares it. If Section A reaches this lesson in week 2 and "
           "Section B in week 4, one deadline cannot serve both — and on-time submission is the whole "
           "point of an assignment. The fix is a `GROUP_ASSIGNMENTS (group_id, assignment_id, "
           "due_date)` junction (ERD Open Question 1). Decide before building.")
add("/lessons/{lessonId}/assignments","get",op(T,"listAssignments","List assignments",
 "Homework attached to a lesson.\n\nAssignments live on the **curriculum branch**: authored once "
 "against a lesson, seen by every group taking the course. They are checked for on-time submission "
 "and never scored.","I, A, S","own-course / own-enrollment","08, 20",OK,
 params=[LID],ok=page("Assignment")))
add("/lessons/{lessonId}/assignments","post",op(T,"createAssignment","Create an assignment",
 "New homework for a lesson.","I","own-course","08",OQ1,
 params=[LID],body=ref("AssignmentCreate"),ok=ref("Assignment"),ok_code="201",errors=["400","409","422"]))
add("/assignments/{assignmentId}","get",op(T,"getAssignment","Get an assignment",
 "The WF 23 header and deadline.","I, A, S","own-course / own-enrollment","23",OK,
 params=[AID],ok=ref("Assignment"),errors=["404"]))
add("/assignments/{assignmentId}","patch",op(T,"updateAssignment","Update an assignment",
 "Title, description or due date.","I","own-course","08",OQ1,
 params=[AID],body=ref("AssignmentUpdate"),ok=ref("Assignment"),errors=["400","404","422"]))
add("/assignments/{assignmentId}","delete",op(T,"deleteAssignment","Delete an assignment",
 "**Returns 409 once any student has submitted.** `ASSIGNMENTS → ASSIGNMENT_SUBMISSIONS` is "
 "`RESTRICT`: student work is never silently destroyed.","I","own-course","08",OK,
 params=[AID],ok_code="204",errors=["404","409"]))
add("/lessons/{lessonId}/assignments/order","put",op(T,"reorderAssignments","Reorder assignments",
 "**Bulk**, within one lesson.","I","own-course","08",OK,
 params=[LID],body=ref("ReorderRequest"),ok=arr("Assignment"),errors=["400","409"]))
add("/assignments/{assignmentId}/solution","put",op(T,"uploadSolution","Upload the solution",
 "Attaches the solution file. This is WF 15's \"+ Upload homework solutions\", and it is the only "
 "homework write a TA makes.\n\nRequires `can_upload_solutions`, **not** `can_grade` — they are "
 "separate permissions.","I, A","own-course / assigned-group + can_upload_solutions","15",OK,
 params=[AID],body=ref("SolutionUpload"),ok=ref("Assignment"),errors=["400","404"]))
add("/assignments/{assignmentId}/solution/release","post",op(T,"releaseSolution","Release the solution",
 "Stamps `solution_released_at`, making the solution visible to students so they can self-check.\n\n"
 "The solution may not be released before the deadline — `solution_released_at >= due_date` is a "
 "CHECK constraint, because releasing answers early defeats the assignment.",
 "I, A","own-course / assigned-group + can_upload_solutions","15",OK,
 params=[AID],ok=ref("Assignment"),errors=["404","422"]))
add("/assignments/{assignmentId}/submissions","post",op(T,"submitAssignment","Submit homework",
 "Uploads the completed sheet with an optional note to the teacher. The server computes `is_late` "
 "against `due_date` at submission time; it is stored, not derived on read, and never changes.",
 "S","own-enrollment","23",OK,
 params=[AID],body=ref("AssignmentSubmissionCreate"),ok=ref("AssignmentSubmission"),
 ok_code="201",errors=["400","404","409"]))
add("/assignments/{assignmentId}/submissions/mine","put",op(T,"resubmitAssignment","Re-submit homework",
 "Replaces the caller's existing submission **in place** — `UNIQUE (assignment_id, student_id)` means "
 "one row per student, so re-submission overwrites rather than versioning.","S","self","23",
 WARN("Nothing locks this yet. WF 23 says re-submission is open \"until the instructor grades it\", "
      "but assignments have no grading step any more, so the lock needs a new trigger. "
      "`solution_released_at` is the recommended one (ERD Open Question 3)."),
 params=[AID],body=ref("AssignmentSubmissionCreate"),ok=ref("AssignmentSubmission"),
 errors=["400","404","409"]))
add("/assignments/{assignmentId}/submissions","get",op(T,"listAssignmentSubmissions","List submissions",
 "Who handed in, who was late, and — by absence — who is missing.\n\nThe three states WF 11 shows are "
 "derived: **Submitted** is a row with `is_late = false`, **Late** is a row with `is_late = true`, "
 "**Missing** is no row once the deadline has passed.","I, A","own-course / assigned-group","11",OK,
 params=[AID,P("status","Filter to one derived state.","query",
   {"type":"string","enum":["submitted","late","missing"]},False),LIMIT,CURSOR],
 ok=page("AssignmentSubmission")))

# ============================ GROUPS & ASSISTANTS ============================
T="Groups"
GID = P("groupId","The group. The wireframes call this a \"section\".")
add("/courses/{courseId}/groups","get",op(T,"listGroups","List groups",
 "The course's sections — \"Section A\", \"Section B\", \"Revision\".\n\n**Vocabulary:** the "
 "wireframes say *section*; the schema says `GROUPS`. They are the same thing.",
 "I, A","own-course / assigned-group","09, 11, 13",OK,params=[CID],ok=page("Group")))
add("/courses/{courseId}/groups","post",op(T,"createGroup","Create a group","Adds a section.",
 "I","own-course","09",OK,params=[CID],body=ref("GroupCreate"),ok=ref("Group"),
 ok_code="201",errors=["400"]))
add("/groups/{groupId}","get",op(T,"getGroup","Get a group","Section header and defaults.",
 "I, A","assigned-group","11",OK,params=[GID],ok=ref("Group"),errors=["404"]))
add("/groups/{groupId}","patch",op(T,"updateGroup","Update a group",
 "Name, default schedule hint, default room, capacity.","I","own-course","09",
 WARN("`schedule_info` and `classroom_location` are **defaults, not truth** — the authoritative "
      "time and place live on each `LIVE_SESSIONS` row. No screen edits them, and no screen shows "
      "`max_capacity` (gaps B12, B13)."),
 params=[GID],body=ref("GroupUpdate"),ok=ref("Group"),errors=["400","404"]))
add("/groups/{groupId}/archive","post",op(T,"archiveGroup","Archive a group",
 "**There is no group delete.** `GROUPS → LIVE_SESSIONS` and `GROUPS → QUIZZES` are both `RESTRICT`, "
 "so a cohort with history cannot be removed. Archiving is the supported operation.",
 "I","own-course","—",WARN("No screen offers this; deletion versus archival is undecided (gap D26)."),
 params=[GID],ok=ref("Group"),errors=["404","409"]))
add("/groups/{groupId}/students","get",op(T,"listGroupStudents","List enrolled students",
 "The section roster.","I, A","assigned-group","10, 11, 16",OK,
 params=[GID,LIMIT,CURSOR],ok=page("Student")))
add("/groups/{groupId}/students","post",op(T,"enrollStudents","Enroll students",
 "**Bulk** — the body takes an array, because enrolling a section one student at a time does not "
 "scale to 150+.","I","own-course","11",
 WARN("`max_capacity` exists but no screen surfaces a \"group full\" state (gap B12)."),
 params=[GID],body=ref("EnrollRequest"),ok=arr("Student"),ok_code="201",errors=["400","409"]))
add("/groups/{groupId}/students/{studentId}","delete",op(T,"unenrollStudent","Unenroll a student",
 "Removes the `STUDENT_GROUPS` row.","I","own-course","11",
 WARN("Group membership is current-state only — there is no enrollment history, so removing a "
      "student changes how past session rosters are reconstructed (gaps E7, C14)."),
 params=[GID,P("studentId","The student.")],ok_code="204",errors=["404"]))
T="Assistants"
UIDP = P("userId","The assistant's user id.")
add("/assistants","get",op(T,"listAssistants","List teaching assistants",
 "The WF 13 team table: each TA with their scope and permissions.\n\n**Scope** is which groups the "
 "TA has rows for; \"All sections\" is stored as N rows, not a wildcard. **Permissions** are the "
 "three booleans matching the invite-time checkboxes exactly: `can_take_attendance`, `can_grade`, "
 "`can_upload_solutions`.","I","own-course","13",OK,
 params=[P("include_revoked","Include revoked assistants.","query",{"type":"boolean","default":False},False),
   LIMIT,CURSOR],ok=page("Assistant")))
add("/assistants/{userId}","get",op(T,"getAssistant","Get one assistant",
 "One TA's groups and flags.","I","own-course","13",OK,
 params=[UIDP],ok=ref("Assistant"),errors=["404"]))
add("/assistants/{userId}","patch",op(T,"updateAssistant","Edit scope and permissions",
 "\"Edit\" on WF 13. Replaces the group set and the three flags in one call.","I","own-course","13",
 WARN("Because \"All sections\" is N rows rather than a wildcard, a TA does **not** inherit access "
      "to groups created later. If the instructor expects inheritance, this needs a wildcard row or "
      "a course-level grant (gaps D10, D37)."),
 params=[UIDP],body=ref("AssistantUpdate"),ok=ref("Assistant"),errors=["400","404"]))
add("/assistants/{userId}/revoke","post",op(T,"revokeAssistant","Revoke an assistant",
 "Sets `is_revoked` on every one of the TA's group rows.\n\n**This is never a row delete.** "
 "`QUIZ_ANSWERS.graded_by_user_id` and `QUIZ_ATTEMPTS.graded_by_user_id` point at this user, and "
 "`USERS → GROUP_ASSISTANTS` is `RESTRICT`. Access ends immediately; every grade they gave keeps its "
 "attribution, exactly as WF 13 requires.","I","own-course","13",OK,
 params=[UIDP],ok=ref("Assistant"),errors=["404"]))
add("/groups/{groupId}/assistants","get",op(T,"listGroupAssistants","List a group's assistants",
 "Assistants assigned to one section.","I","own-course","13",OK,params=[GID],ok=arr("Assistant")))
add("/groups/{groupId}/assistants/{userId}","put",op(T,"assignAssistant","Assign to a group",
 "Creates or replaces the `GROUP_ASSISTANTS` row for this TA and group, with its three flags.",
 "I","own-course","13",OK,params=[GID,UIDP],body=ref("AssistantPermissions"),
 ok=ref("Assistant"),errors=["400","404"]))
add("/groups/{groupId}/assistants/{userId}","delete",op(T,"unassignAssistant","Unassign from a group",
 "Sets `is_revoked` on this one row rather than deleting it, for the reason above.",
 "I","own-course","13",OK,params=[GID,UIDP],ok_code="204",errors=["404"]))

# ============================ SCHEDULING ============================
T="Scheduling"
SID = P("sessionId","The live session.")
G10 = WARN("**Recurrence is not modelled (G10), and this is shape-defining.** WF 09 sets recurring "
           "sessions weekly per section, and editing one occurrence prompts \"this session only\" vs "
           "\"this and following\". `LIVE_SESSIONS` rows are independent and `GROUPS.schedule_info` is "
           "explicitly a free-text hint. Either occurrences are materialized on create — which adds a "
           "`scope=this|this_and_following` parameter to the update — or a `SESSION_SERIES` parent is "
           "introduced. Decide before implementing; it changes the whole session-write API.")
add("/live-sessions","get",op(T,"listLiveSessions","List sessions",
 "**The timetable query**, mirroring the index `LIVE_SESSIONS (group_id, scheduled_start)`. Serves "
 "the instructor calendar, the dashboard's \"today\" strip, the TA's sessions, and the student and "
 "parent schedule views.","I, A, S, P","role-shaped","09, 06, 14, 19, 18",OK,
 params=[P("from","Window start (inclusive), ISO-8601.","query",{"type":"string","format":"date-time"},False),
   P("to","Window end (exclusive), ISO-8601.","query",{"type":"string","format":"date-time"},False),
   P("group_id","Filter to one section.","query",None,False),
   P("course_id","Filter to one course.","query",None,False),
   P("mode","`ONSITE` or `ONLINE`.","query",ref("SessionMode"),False),
   P("status","Filter by status.","query",ref("SessionStatus"),False),LIMIT,CURSOR],
 ok=page("LiveSession")))
add("/live-sessions","post",op(T,"createLiveSession","Schedule a session",
 "\"+ New Session\" on WF 09. The online/offline toggle maps to `mode`, which drives two validation "
 "rules: `ONLINE` requires `meeting_url`, `ONSITE` requires `classroom_location`.\n\nIf `lesson_id` "
 "is set it must belong to the group's course — a section can only cover lessons from its own "
 "course. `lesson_id` is nullable on purpose: revision, exam prep and Q&A classes map to no lesson.",
 "I","own-course","09",G10,body=ref("LiveSessionCreate"),ok=ref("LiveSession"),
 ok_code="201",errors=["400","422"]))
add("/live-sessions/{sessionId}","get",op(T,"getLiveSession","Get a session",
 "Session detail for the Class Session View.","I, A","assigned-group","10, 16, 21",OK,
 params=[SID],ok=ref("LiveSession"),errors=["404"]))
add("/live-sessions/{sessionId}","patch",op(T,"updateLiveSession","Update a session",
 "Change time, room, mode or the linked lesson.","I","own-course","09",G10,
 params=[SID],body=ref("LiveSessionUpdate"),ok=ref("LiveSession"),errors=["400","404","422"]))
add("/live-sessions/{sessionId}/cancel","post",op(T,"cancelLiveSession","Cancel a session",
 "Sets `status = CANCELLED`.","I","own-course","—",
 WARN("The enum value exists but no screen offers the action, and whether cancelled sessions stay in "
      "the attendance denominator is undecided (gaps B14, D15)."),
 params=[SID],ok=ref("LiveSession"),errors=["404"]))
add("/live-sessions/{sessionId}/join","get",op(T,"getJoinInfo","Get join information",
 "Returns the embed target and whether the join window is open. Drives WF 19's \"Join Now\" button, "
 "which activates only inside the window and otherwise shows a countdown.","S","own-enrollment","19, 21",
 BLOCK("no join-window or early-join field exists (gap A15), and `meeting_url` is a plain string with "
       "no provider or external meeting id (G15)."),
 params=[SID],ok=ref("JoinInfo"),errors=["404","409"]))
add("/webhooks/meetings/{provider}","post",op(T,"meetingWebhook","Meeting provider webhook",
 "Ingests a provider join log to auto-mark attendance for online sessions. Authenticated by "
 "signature, not by bearer token.","—","signature","10, 21",
 BLOCK("no provider, credential or external-meeting-id representation exists (G15). Auto-generated "
       "links and join-log attendance are out of scope until an integration is modelled."),
 params=[P("provider","`zoom` or `meet`.",schema={"type":"string","enum":["zoom","meet"]})],
 body=ref("MeetingWebhook"),ok_code="204",errors=["400"],public=True))

# ============================ ATTENDANCE ============================
T="Attendance"
add("/live-sessions/{sessionId}/attendance","get",op(T,"getAttendance","Get the attendance roster",
 "One row per student with any recorded status.\n\n**Read this carefully for past sessions.** Group "
 "membership is current-state only — there is no enrollment history. The response is therefore built "
 "from recorded `ATTENDANCE` rows **unioned with** current membership, not from membership alone; "
 "otherwise a student who has since left the section vanishes from a class they attended.",
 "I, A","assigned-group + can_take_attendance","10, 16",
 WARN("See the union note above (gaps E7, C14)."),params=[SID],ok=ref("AttendanceSheet"),errors=["404"]))
add("/live-sessions/{sessionId}/attendance","put",op(T,"saveAttendance","Save attendance",
 "**Bulk.** The body is the full status array for the session — this single endpoint serves both "
 "\"Mark all present\" and \"Save Attendance\". Idempotent, and upserts against "
 "`UNIQUE (student_id, live_session_id)`.","I, A","assigned-group + can_take_attendance","10, 16",OK,
 params=[SID],body=ref("AttendanceSave"),ok=ref("AttendanceSheet"),errors=["400","404","422"]))
add("/attendance/{attendanceId}","patch",op(T,"overrideAttendance","Override one student",
 "Single-student correction.","I, A","assigned-group + can_take_attendance","10",
 WARN("`ATTENDANCE` has no `recorded_by` column, so an override is indistinguishable from the "
      "original mark. Which value wins when auto-marking and manual marking disagree, and when "
      "reconciliation happens, is undecided (gap D5)."),
 params=[P("attendanceId","The attendance record.")],body=ref("AttendanceUpdate"),
 ok=ref("AttendanceRecord"),errors=["400","404"]))
add("/live-sessions/{sessionId}/end","post",op(T,"endSession","End session and save attendance",
 "Commits attendance and sets `status = COMPLETED`.\n\n**This is the fan-out trigger.** WF 10 states "
 "that ending a session is what instantly updates the parent's attendance badges (WF 17) and the "
 "child detail view (WF 18). It emits `attendance.saved` on the event stream.",
 "I, A","assigned-group + can_take_attendance","10",OK,
 params=[SID],body=ref("AttendanceSave"),ok=ref("LiveSession"),errors=["400","404"]))
add("/live-sessions/{sessionId}/attendance/self","post",op(T,"markSelfPresent","Auto-mark on join",
 "Marks the calling student present when they join the embedded live class (WF 21).",
 "S","own-enrollment","21",
 BLOCK("WF 21 says leaving early \"can flag partial attendance\", but `ATTENDANCE.status` is "
       "`PRESENT / ABSENT / LATE` with no `PARTIAL` value and no join or leave timestamps (G13). "
       "It also collides with manual marking — see gap D5."),
 params=[SID],ok=ref("AttendanceRecord"),errors=["404","409"]))

# ============================ QUIZZES ============================
T="Quizzes"
QID = P("quizId","The quiz.")
QQID = P("questionId","The question.")
D1 = WARN("A quiz is authored **inside a lesson** on WF 08, but it is group-scoped by design and no "
          "screen asks which section it is for (gap D1). This path makes the group explicit: "
          "authoring one quiz for three sections is three calls. Assignments no longer carry this "
          "ambiguity — they are natively lesson-scoped.")
add("/quizzes","get",op(T,"listQuizzes","List quizzes",
 "Mirrors the index `QUIZZES (group_id, closes_at)` — the \"due soon\" query.\n\nQuizzes live on the "
 "**cohort branch**: issued to one group, with an open/close window and a per-attempt clock.",
 "I, A, S","role-shaped","06, 14, 19",OK,
 params=[P("group_id","Filter to one section.","query",None,False),
   P("lesson_id","Filter by the optional lesson tag.","query",None,False),
   P("closes_before","Only quizzes closing before this instant.","query",
     {"type":"string","format":"date-time"},False),LIMIT,CURSOR],ok=page("Quiz")))
add("/groups/{groupId}/quizzes","post",op(T,"createQuiz","Create a quiz",
 "`opens_at` and `closes_at` are the availability window; `duration_seconds` is the clock that "
 "starts when a student begins. A quiz may be open for a week but allow 30 minutes once started — "
 "either bound may bind first. Omit `duration_seconds` for an untimed quiz.\n\nIf `lesson_id` is set "
 "it is **tagging only** and must belong to the group's course; it does not move the quiz onto the "
 "curriculum branch.","I","own-course","08",D1,
 params=[GID],body=ref("QuizCreate"),ok=ref("Quiz"),ok_code="201",errors=["400","422"]))
add("/quizzes/{quizId}","get",op(T,"getQuiz","Get a quiz",
 "Detail with questions, for the builder.","I, A","own-course","08, 15",OK,
 params=[QID],ok=ref("QuizDetail"),errors=["404"]))
add("/quizzes/{quizId}","patch",op(T,"updateQuiz","Update a quiz",
 "Edit the window, the duration or the title.","I","own-course","08",D1,
 params=[QID],body=ref("QuizUpdate"),ok=ref("Quiz"),errors=["400","404","422"]))
add("/quizzes/{quizId}","delete",op(T,"deleteQuiz","Delete a quiz",
 "**Returns 409 once any student has attempted it.** `QUIZZES → QUIZ_ATTEMPTS` is `RESTRICT`.",
 "I","own-course","08",OK,params=[QID],ok_code="204",errors=["404","409"]))
add("/quizzes/{quizId}/questions","get",op(T,"listQuestions","List questions",
 "In `order_index` order — the order the WF 22 navigator uses.","I, A","own-course","08",OK,
 params=[QID],ok=arr("QuizQuestion")))
add("/quizzes/{quizId}/questions","post",op(T,"createQuestion","Add a question",
 "`MCQ` carries `options` and a `model_answer` and is auto-scored at submit. `STRUCTURED` carries a "
 "`model_answer` for the grader's reference and always needs a human.","I","own-course","08",OK,
 params=[QID],body=ref("QuizQuestionCreate"),ok=ref("QuizQuestion"),ok_code="201",errors=["400","409"]))
add("/questions/{questionId}","patch",op(T,"updateQuestion","Update a question","Edit in place.",
 "I","own-course","08",OK,params=[QQID],body=ref("QuizQuestionUpdate"),ok=ref("QuizQuestion"),
 errors=["400","404"]))
add("/questions/{questionId}","delete",op(T,"deleteQuestion","Delete a question","Removes it.",
 "I","own-course","08",OK,params=[QQID],ok_code="204",errors=["404"]))
add("/quizzes/{quizId}/questions/order","put",op(T,"reorderQuestions","Reorder questions",
 "**Bulk.** Drives the navigator order on WF 22.","I","own-course","08",OK,
 params=[QID],body=ref("ReorderRequest"),ok=arr("QuizQuestion"),errors=["400","409"]))

# ============================ ATTEMPTS ============================
T="Quiz attempts"
ATID = P("attemptId","The attempt.")
add("/quizzes/{quizId}/attempts","post",op(T,"startAttempt","Start an attempt",
 "Begins the quiz. Sets `started_at` and **materializes** `expires_at` as "
 "`min(started_at + duration_seconds, quiz.closes_at)`.\n\nThe expiry is stored rather than "
 "recomputed on every read so the countdown, the auto-submit and late-answer rejection all agree on "
 "one authoritative instant.\n\n`UNIQUE (quiz_id, student_id)` means one attempt per student — "
 "**retakes are not modelled**. A second call returns 409.","S","own-enrollment","22",OK,
 params=[QID],ok=ref("AttemptDetail"),ok_code="201",errors=["404","409"]))
add("/attempts/{attemptId}","get",op(T,"getAttempt","Resume an attempt",
 "Answers saved so far, seconds remaining, and a per-question answered flag for the navigator.",
 "S","self","22",OK,params=[ATID],ok=ref("AttemptDetail"),errors=["404"]))
add("/attempts/{attemptId}/answers","patch",op(T,"saveAnswers","Autosave answers",
 "Upserts one or more answers against `UNIQUE (attempt_id, question_id)`. Called as the student "
 "moves between questions.\n\nReturns `409 ATTEMPT_EXPIRED` past `expires_at`.","S","self","22",OK,
 params=[ATID],body=ref("AnswerSaveRequest"),ok=ref("AttemptDetail"),errors=["400","404","409"]))
add("/attempts/{attemptId}/submit","post",op(T,"submitAttempt","Submit an attempt",
 "Finalizes. Auto-scores every `MCQ` answer into `auto_score` and sets `status = SUBMITTED`. "
 "Structured answers enter the grading queue.","S","self","22",
 WARN("What happens at timer expiry — auto-submit, hard lock, or a grace period — is undecided "
      "(gap D17). The schema supports all three."),
 params=[ATID],ok=ref("AttemptResult"),errors=["404","409"]))
add("/attempts/{attemptId}/result","get",op(T,"getAttemptResult","Get the result",
 "The student's post-submit view.\n\nThis is where \"MCQ score shows immediately; overall grade "
 "stays pending until a human grades it\" is served: `auto_score` is populated at submit, "
 "`total_score` stays null until grading completes. The response carries `grading_status` "
 "explicitly so the client renders \"pending\" rather than inferring it from a null.",
 "S","self","22",OK,params=[ATID],ok=ref("AttemptResult"),errors=["404"]))

# ============================ GRADING ============================
T="Grading"
ANID = P("answerId","The answer.")
GRD = ("**Authorization.** Every endpoint in this group requires `can_grade` on the group that owns "
       "the answer, resolved through `attempt → quiz → group`, with `is_revoked = false`. The course's "
       "owning instructor always passes. A TA with \"Attendance only\" gets `403 INSUFFICIENT_SCOPE`.")
add("/grading/queue","get",op(T,"getGradingQueue","Get the grading queue",
 "**The WF 15 dashboard.** Ungraded structured answers across every group the caller may grade.\n\n"
 "The queue is a *query, not a table*: `QUIZ_ANSWERS` where `points_awarded IS NULL`, joined to "
 "`QUIZ_QUESTIONS` on `question_type = 'STRUCTURED'` and to `GROUP_ASSISTANTS` for scope. The partial "
 "index `QUIZ_ANSWERS (attempt_id) WHERE points_awarded IS NULL` exists for exactly this.\n\n"
 "**The unit of work is one answer, not one attempt.** WF 15 serves \"Youssef T. — Q4 (structured "
 "answer)\" with its own score box. Two TAs may legitimately grade different questions of the same "
 "student's paper, which is why grader attribution lives on the answer.\n\nEach item carries the "
 "student, the question text, the points available, the student's answer and the `model_answer`.\n\n"
 + GRD,"I, A","assigned-group + can_grade","15",OK,
 params=[P("quiz_id","Filter to one quiz.","query",None,False),
   P("group_id","Filter to one section.","query",None,False),
   P("course_id","Filter to one course.","query",None,False),LIMIT,CURSOR],
 ok=page("GradingQueueItem")))
add("/grading/summary","get",op(T,"getGradingSummary","Get pending counts",
 "Counts for the badges — pending answers per quiz and per group. Backs WF 06's \"24 pending\" tile "
 "and the WF 14 TA dashboard.\n\n" + GRD,"I, A","assigned-group + can_grade","06, 14, 15",OK,
 ok=ref("GradingSummary")))
add("/grading/queue/next","get",op(T,"getNextGradingItem","Serve the next item",
 "Returns the next ungraded answer and takes a **soft claim** on it — `claimed_by_user_id` and "
 "`claimed_at`. This is what makes \"Skip\" work without re-serving the same essay to the same "
 "grader.\n\n" + GRD,"I, A","assigned-group + can_grade","15",
 WARN("The claim is advisory, expires after a few minutes, and never blocks a grade. It exists "
      "because WF 13 shows two TAs and the persona has 150+ students, so concurrent grading is real. "
      "If only one person ever grades, drop this endpoint, `/skip`, and both claim columns, and page "
      "through `/grading/queue` instead."),
 params=[P("quiz_id","Restrict to one quiz.","query",None,False)],
 ok=ref("GradingQueueItem"),errors=["404"]))
add("/grading/queue/{answerId}/skip","post",op(T,"skipGradingItem","Skip an item",
 "Releases the claim and returns the answer to the pool.\n\n" + GRD,
 "I, A","assigned-group + can_grade","15",
 WARN("See `GET /grading/queue/next` — the claim model is optional."),
 params=[ANID],ok_code="204",errors=["404"]))
add("/answers/{answerId}/grade","patch",op(T,"gradeAnswer","Grade one answer",
 "**\"Save\" on WF 15.** Writes `points_awarded` and an optional `evaluator_comment`, stamps "
 "`graded_by_user_id` and `graded_at`, and clears any claim.\n\nThree validation rules apply:\n\n"
 "- `0 <= points_awarded <= question.points` → `422 POINTS_EXCEED_QUESTION`\n"
 "- only `STRUCTURED` answers are human-graded → `422 NOT_MANUALLY_GRADABLE` on an MCQ\n"
 "- the grader must hold `can_grade` on the answer's group → `403`\n\n" + GRD,
 "I, A","assigned-group + can_grade","15",OK,
 params=[ANID],body=ref("GradeAnswerRequest"),ok=ref("QuizAnswer"),errors=["400","404","422"]))
add("/grading/answers","patch",op(T,"gradeAnswersBulk","Grade answers in bulk",
 "**Bulk save.** An array of `{answer_id, points_awarded, evaluator_comment}`.\n\nOne round trip per "
 "essay is the wrong shape at 150+ students; this is the endpoint a grading session should actually "
 "use. Partial success is reported per item rather than failing the whole batch.\n\n" + GRD,
 "I, A","assigned-group + can_grade","15",OK,
 body=ref("BulkGradeRequest"),ok=ref("BulkGradeResult"),errors=["400","422"]))
add("/quizzes/{quizId}/attempts","get",op(T,"listQuizAttempts","List attempts for a quiz",
 "Per-quiz grading view: every attempt with its pending-answer count. Backs WF 15's "
 "\"Quiz — Kinematics (24 pending)\" header and the \"18/24 already complete\" line.\n\n" + GRD,
 "I, A","assigned-group + can_grade","15",OK,
 params=[QID,P("status","Filter by attempt status.","query",ref("AttemptStatus"),False),LIMIT,CURSOR],
 ok=page("QuizAttempt")))
add("/attempts/{attemptId}/finalize","post",op(T,"finalizeAttempt","Finalize grading",
 "Computes `total_score` as the sum of all `points_awarded`, sets `status = GRADED`, stamps the "
 "attempt's `graded_by_user_id` and `graded_at`, and fires the student and parent fan-out "
 "(`quiz.graded`).\n\nReturns `409 ATTEMPT_INCOMPLETE` if any structured answer is still ungraded.\n\n"
 + GRD,"I, A","assigned-group + can_grade","15",
 WARN("**Auto-finalize or explicit?** Either the last `PATCH /answers/{id}/grade` on an attempt flips "
      "it to `GRADED` automatically, or finalize stays a deliberate second step so a grader can review "
      "the whole paper before releasing it. Auto-finalize fits WF 15 better — its queue is "
      "answer-at-a-time across many students and never shows a whole paper — with this endpoint kept "
      "as an instructor override. Undecided; it changes whether the fan-out has one trigger or two "
      "(gap D38). Regrades also overwrite rather than append, so a TA's original score is lost when an "
      "instructor overrides it (gap D9)."),
 params=[ATID],ok=ref("QuizAttempt"),errors=["404","409"]))

# ============================ ROSTER & DASHBOARDS ============================
T="Roster"
STID = P("studentId","The student.")
add("/students","get",op(T,"listStudents","List students",
 "The WF 11 roster — 158 rows with attendance %, last quiz %, and homework state. Every aggregate "
 "here is computed on read and never stored.","I, A","own-course","11",
 WARN("Three unresolved dependencies. The `Section` column assumes one group per student, but "
      "`STUDENT_GROUPS` is many-to-many (gaps C13, D4). \"Missing\" homework is the absence of a "
      "submission row past the deadline — derivable now, but which assignments a student is expected "
      "to have done depends on ERD Open Question 1. And the attendance-% denominator is undefined "
      "until cancelled-session handling is settled (gaps C16, D15)."),
 params=[P("group_id","Filter to one section.","query",None,False),
   P("attendance_below","Only students below this attendance percentage.","query",
     {"type":"integer","minimum":0,"maximum":100},False),
   P("homework_status","`submitted`, `late` or `missing`.","query",
     {"type":"string","enum":["submitted","late","missing"]},False),
   P("q","Free-text name search.","query",{"type":"string"},False),LIMIT,CURSOR],
 ok=page("StudentRosterRow")))
add("/students/{studentId}","get",op(T,"getStudent","Get a student",
 "The per-student detail panel: full attendance history, quiz and homework record, and linked parent "
 "contacts — the single view meant to replace WhatsApp back-and-forth with parents.",
 "I, A","own-course","11",
 WARN("A child may now have several linked parents, but WF 11 shows *the* parent contact. Whether "
      "the panel lists all links or one designated primary is undecided (gap D33)."),
 params=[STID],ok=ref("StudentDetail"),errors=["404"]))
add("/students/{studentId}/attendance","get",op(T,"getStudentAttendance","Student attendance history",
 "Per-session attendance for one student.","I, A, P","own-course / linked-child","11, 18",OK,
 params=[STID,LIMIT,CURSOR],ok=page("AttendanceRecord")))
add("/students/{studentId}/grades","get",op(T,"getStudentGrades","Student grade history",
 "Graded quiz attempts for one student.","I, A, P","own-course / linked-child","11, 18",OK,
 params=[STID,LIMIT,CURSOR],ok=page("AttemptResult")))
T="Dashboards"
add("/dashboards/instructor","get",op(T,"getInstructorDashboard","Instructor dashboard",
 "WF 06 — stat cards, today's sessions, and the pending-grading count.","I","own-course","06",
 BLOCK("**the four stat-card labels are blank placeholder bars in the wireframe source.** Only three "
       "deep-link targets are named (roster, courses, schedule); the fourth metric is undefined, and "
       "none of the four say what they count (gap C3). This is a documentation gap, not a data one — "
       "the endpoint cannot be specified until someone names the numbers."),
 ok=ref("InstructorDashboard")))
add("/dashboards/assistant","get",op(T,"getAssistantDashboard","TA dashboard",
 "WF 14 — assigned sections, pending grading count, and today's sessions to cover.",
 "A","assigned-group","14",
 BLOCK("`GROUP_ASSISTANTS` assigns a TA to a **group**, not to a session. \"Today's sessions to "
       "cover\" implies a per-session assignment that does not exist (gap C15). The assigned-sections "
       "and pending-count halves are specifiable today."),ok=ref("AssistantDashboard")))
add("/dashboards/student","get",op(T,"getStudentDashboard","Student dashboard",
 "WF 19 — next session with its join state, work due soon across all enrolled courses, and recent "
 "grades.","S","own-enrollment","19",
 WARN("\"Recent grade — Homework 1.1 — 8/10\" cannot be served: assignments are checked for on-time "
      "submission and are not scored. Either the screen shows a submitted/late chip instead, or "
      "assignment submissions regain an optional score (ERD Open Question 2). The join-state half "
      "depends on gap A15."),ok=ref("StudentDashboard")))
add("/dashboards/parent","get",op(T,"getParentDashboard","Parent home",
 "WF 17 — one card per linked child plus the recent-updates feed.","P","linked-child","17",
 WARN("The fee badge on each card depends on G2; everything else is specifiable."),
 ok=ref("ParentDashboard")))

# ============================ FEES ============================
T="Fees"
G2 = BLOCK("no student-payment entity exists anywhere (G2). `COURSES.fees` is one static decimal and "
           "`SUBSCRIPTIONS` is a **different money flow** — instructor → platform, not student → "
           "instructor. Before any of this can be built, gap D19 must be answered: WF 12 shows a "
           "per-student \"Plan: Monthly\" column while `COURSES.fees` is a single decimal, so are fees "
           "per course, per group, per month, or per student? The proposed shape is `ENROLLMENT_FEES` "
           "(student × group × period, status `PAID/DUE/OVERDUE`) plus `PAYMENTS`.")
FID = P("feeId","The fee record.")
add("/fees/summary","get",op(T,"getFeeSummary","Revenue summary",
 "WF 12's three tiles: \"This month\", \"Outstanding\", and \"Paid on time 91%\".","I","own-course","12",
 G2,ok=ref("FeeSummary")))
add("/fees","get",op(T,"listFees","List student fees",
 "Per-student fee rows: student, section, plan and status.","I","own-course","12",G2,
 params=[P("status","`paid`, `due` or `overdue`.","query",
   {"type":"string","enum":["paid","due","overdue"]},False),
   P("group_id","Filter to one section.","query",None,False),LIMIT,CURSOR],ok=page("Fee")))
add("/fees/{feeId}/remind","post",op(T,"sendFeeReminder","Send a payment reminder",
 "Notifies the linked parent directly rather than the instructor chasing payment (WF 12). Emits "
 "`notification.created`.","I","own-course","12",
 BLOCK("G2, plus a second problem: a child may now have several linked parents, but this action is "
       "singular. Whether the reminder fans out to every link or goes to one designated primary is "
       "undecided (gap D33)."),params=[FID],ok_code="202",errors=["404"]))
add("/fees/{feeId}/receipt","get",op(T,"getReceipt","Get a receipt",
 "Receipt for a paid fee.","I, P","own-course / linked-child","12, 18",G2,
 params=[FID],ok=ref("Receipt"),errors=["404"]))
add("/payments","post",op(T,"createPayment","Pay a fee",
 "Parent-side payment. Clears the overdue badge on Parent Home in real time (`fee.paid`).\n\n"
 "**This is the only write a parent is permitted anywhere in the API.**","P","linked-child","18",G2,
 body=ref("PaymentCreate"),ok=ref("Payment"),ok_code="201",errors=["400","422"]))

# ============================ PARENT PORTAL ============================
T="Parent portal"
CHILD = P("studentId","The linked child.")
PN = ("Two invariants govern every endpoint here, both enforced in the service layer:\n\n"
      "1. **A parent reads nothing outside their linked children.** Every query is filtered by "
      "`PARENT_STUDENTS (parent_user_id = caller)`. No parent-visible endpoint accepts a "
      "`student_id` without this check.\n"
      "2. **A parent is read-only on academic records.** Attendance, grades and schedule are never "
      "writable by a `PARENT` role. The single parent write in the whole API is fee payment.")
add("/me/children","get",op(T,"listChildren","List linked children",
 "The child switcher on WF 17 — one card per link with attendance %, average grade and fee badge.\n\n"
 "`PARENT_STUDENTS` is many-to-many in both directions: one parent follows several children, and one "
 "child may be followed by both parents. The link is deliberately **not** instructor-scoped — a "
 "parent with children under two instructors holds one account and one set of links.\n\n" + PN,
 "P","linked-child","17",
 WARN("The fee badge depends on G2. Cross-instructor isolation inside one parent account is a "
      "query-time concern the schema does not settle (gap D13)."),ok=arr("ChildSummary")))
add("/children/{studentId}","get",op(T,"getChild","Get a child",
 "Child header and summary for WF 18.\n\n" + PN,"P","linked-child","18",OK,
 params=[CHILD],ok=ref("ChildDetail"),errors=["404"]))
add("/children/{studentId}/attendance","get",op(T,"getChildAttendance","Child attendance tab",
 "Read-only attendance record.\n\n" + PN,"P","linked-child","18",OK,
 params=[CHILD,LIMIT,CURSOR],ok=page("AttendanceRecord")))
add("/children/{studentId}/grades","get",op(T,"getChildGrades","Child grades tab",
 "Read-only grade record.\n\n" + PN,"P","linked-child","18",OK,
 params=[CHILD,LIMIT,CURSOR],ok=page("AttemptResult")))
add("/children/{studentId}/schedule","get",op(T,"getChildSchedule","Child schedule tab",
 "Read-only upcoming sessions.\n\n" + PN,"P","linked-child","18",OK,
 params=[CHILD,P("from","Window start.","query",{"type":"string","format":"date-time"},False),
   P("to","Window end.","query",{"type":"string","format":"date-time"},False)],ok=page("LiveSession")))
add("/children/{studentId}/fees","get",op(T,"getChildFees","Child fees tab",
 "Fee status for one child, and the entry point to payment.\n\n" + PN,"P","linked-child","18",G2,
 params=[CHILD],ok=page("Fee")))

# ============================ NOTIFICATIONS & EVENTS ============================
T="Notifications"
add("/notifications","get",op(T,"listNotifications","List notifications",
 "The persisted feed behind WF 17's \"Recent updates\". Mirrors the index "
 "`NOTIFICATIONS (user_id, is_read)`.","all","self","17",
 WARN("WF 17 promises that tapping an update \"deep-links to the specific session or quiz\", but "
      "`NOTIFICATIONS` has title, message and type only — no `target_type` or `target_id` (gaps A23, "
      "C18). The feed renders; the deep-link does not. Delivery is in-app only; email and push are "
      "out of scope (gap D22)."),
 params=[P("is_read","Filter read or unread.","query",{"type":"boolean"},False),LIMIT,CURSOR],
 ok=page("Notification")))
add("/notifications/read","post",op(T,"markNotificationsRead","Mark notifications read",
 "**Bulk.** Marks the given ids read, or all of them when `all` is true.","all","self","17",OK,
 body=ref("MarkReadRequest"),ok_code="204",errors=["400"]))
add("/events","get",op("Events","streamEvents","Subscribe to live updates",
 "**Server-Sent Events.** The transport behind every \"instantly\" and \"in real time\" promise in "
 "the wireframes. Responds with `text/event-stream`; each event carries a `type` and a JSON payload.\n\n"
 "| Trigger | Event | Lands on |\n|---|---|---|\n"
 "| `POST /live-sessions/{id}/end` | `attendance.saved` | WF 17 badges, WF 18 |\n"
 "| `POST /attempts/{id}/finalize` | `quiz.graded` | WF 22, WF 18 |\n"
 "| `POST /lessons/{id}/publish` | `content.published` | WF 20, WF 17 |\n"
 "| `POST /assignments/{id}/solution/release` | `content.published` | WF 20 |\n"
 "| `POST` or `PATCH /live-sessions` | `schedule.changed` | WF 19, WF 17 |\n"
 "| `POST /payments` | `fee.paid` | WF 17 badge clears |\n"
 "| `POST /fees/{id}/remind` | `notification.created` | WF 17 |\n\n"
 "Events are scoped to the caller: a parent receives only events about linked children, a student "
 "only their own.","all","self","08, 09, 10, 15, 16, 17, 18",
 WARN("The scope document asserts real-time synchronization on seven screens but never specifies the "
      "mechanism (gap D23). SSE is the proposal here because all seven flows are one-way and "
      "read-only, which is exactly what SSE is for. WebSocket would also work and costs more."),
 ok=ref("EventStream")))

# ============================ STUDENT PORTAL ============================
T="Student portal"
add("/me/courses","get",op(T,"listMyCourses","My courses",
 "Courses the caller is enrolled in, reached through `STUDENT_GROUPS`.\n\nStudents never browse "
 "courses directly — they reach curriculum *through* a group enrollment, which is why these reads "
 "live under `/me`.","S","own-enrollment","19, 20",OK,ok=arr("EnrolledCourse")))
add("/me/courses/{courseId}/lessons","get",op(T,"listMyLessons","My lessons",
 "**Published lessons only**, grouped by chapter, each with its materials, recordings and progress "
 "chip. Drafts are invisible to students and parents.","S","own-enrollment","20",
 BLOCK("doubly. The published filter needs `LESSONS.status` (G3), and the `Done` / `In progress` "
       "chip needs per-student progress data that does not exist (G8, gap C5). Whether a published "
       "material inside a draft lesson is visible is also undecided (gap D2)."),
 params=[CID],ok=arr("LessonProgress")))
add("/me/assignments","get",op(T,"listMyAssignments","My homework",
 "Homework due soon across every enrolled course, sorted by deadline.","S","own-enrollment","19, 23",OK,
 params=[P("due_before","Only work due before this instant.","query",
   {"type":"string","format":"date-time"},False),LIMIT,CURSOR],ok=page("StudentAssignment")))
add("/me/quizzes","get",op(T,"listMyQuizzes","My quizzes",
 "Quizzes open now or opening soon, ordered by `closes_at`.","S","own-enrollment","19, 22",OK,
 params=[P("state","`open`, `upcoming` or `closed`.","query",
   {"type":"string","enum":["open","upcoming","closed"]},False),LIMIT,CURSOR],ok=page("StudentQuiz")))
add("/me/grades","get",op(T,"listMyGrades","My grades",
 "Recent graded attempts.","S","own-enrollment","19",OK,params=[LIMIT,CURSOR],ok=page("AttemptResult")))
add("/me/schedule","get",op(T,"getMySchedule","My schedule",
 "Next session and upcoming classes, with join state.","S","own-enrollment","19",
 WARN("Join state depends on the missing join-window field (gap A15)."),
 params=[P("from","Window start.","query",{"type":"string","format":"date-time"},False),
   P("to","Window end.","query",{"type":"string","format":"date-time"},False)],ok=page("LiveSession")))

# ============================ SCHEMAS ============================
def S(props, required=None, desc=None):
    o = {"type": "object", "properties": props}
    if required: o["required"] = required
    if desc: o["description"] = desc
    return o
UUID  = {"type":"string","format":"uuid"}
DT    = {"type":"string","format":"date-time","description":"ISO-8601, always UTC."}
DTN   = {"type":"string","format":"date-time","nullable":True}
MONEY = {"type":"string","description":"Decimal as a string, to avoid float loss. Single implied currency."}
SCORE = {"type":"string","nullable":True,"description":"Decimal as a string."}
STR   = {"type":"string"}
STRN  = {"type":"string","nullable":True}
INT   = {"type":"integer"}
BOOL  = {"type":"boolean"}
def E(*v): return {"type":"string","enum":list(v)}

schemas = {
 "Empty": S({}),
 "PageEnvelope": S({"data":{"type":"array","items":{}},"page":S({
   "limit":INT,"cursor":STRN,"next_cursor":STRN,"total":INT})},desc="Standard list envelope."),
 "Error": S({"error":S({"code":STR,"message":STR,"details":{"type":"array","items":S({
   "field":STR,"issue":STR})}},["code","message"])},["error"],
   "One problem shape for every failure. `code` is machine-readable and stable."),
 "ReorderRequest": S({"order":{"type":"array","items":UUID}},["order"],
   "The complete ordered list of ids. The server reassigns every `order_index` in one transaction."),
 "RoleName": E("TEACHER","STUDENT","ASSISTANT","PARENT","ADMIN"),
 "CourseStatus": E("DRAFT","ACTIVE","ARCHIVED"),
 "SessionMode": E("ONSITE","ONLINE"),
 "SessionStatus": E("SCHEDULED","COMPLETED","CANCELLED"),
 "AttendanceStatus": E("PRESENT","ABSENT","LATE"),
 "QuestionType": E("MCQ","STRUCTURED"),
 "AttemptStatus": E("IN_PROGRESS","SUBMITTED","GRADED"),
 "AccessMode": E("VIEW_ONLY","DOWNLOADABLE"),
 # auth
 "LoginRequest": S({"email":{"type":"string","format":"email"},"password":{"type":"string","format":"password"},
   "remember_me":{"type":"boolean","default":False,"description":"Extends refresh-token lifetime only."}},
   ["email","password"]),
 "RefreshRequest": S({"refresh_token":STR},["refresh_token"]),
 "AuthSession": S({"access_token":STR,"refresh_token":STR,"expires_in":INT,
   "roles":{"type":"array","items":{"$ref":"#/components/schemas/RoleName"}},
   "routing_target":{**E("instructor","assistant","parent","student"),
     "description":"Where the client should land. Resolved server-side (WF 01)."}},
   ["access_token","refresh_token","routing_target"]),
 "CurrentUser": S({"id":UUID,"email":STR,"first_name":STR,"last_name":STR,
   "roles":{"type":"array","items":{"$ref":"#/components/schemas/RoleName"}},
   "routing_target":STR}),
 "RegisterRequest": S({"full_name":{**STR,"description":"WF 02 captures one field; `USERS` splits first/last (gap A21)."},
   "email":{"type":"string","format":"email"},"password":{"type":"string","format":"password"},
   "subjects_taught":{"type":"array","items":STR,"description":"Plural on WF 02; `TEACHERS.specialization` is one string (gap A21)."},
   "curriculum":{**E("IGCSE","AMERICAN_DIPLOMA","BOTH"),"description":"No curriculum field exists in the ERD (gap G16)."}},
   ["full_name","email","password"]),
 "ForgotPasswordRequest": S({"email":{"type":"string","format":"email"}},["email"]),
 "ResetPasswordRequest": S({"token":STR,"password":{"type":"string","format":"password"}},["token","password"]),
 "Profile": S({"id":UUID,"email":STR,"first_name":STR,"last_name":STR,"phone":STRN,"bio":STRN,
   "specialization":STRN}),
 "ProfileUpdate": S({"first_name":STR,"last_name":STR,"phone":STR,"bio":STR,"specialization":STR}),
 "UserSession": S({"user_session_id":UUID,"user_agent":STRN,"ip_address":STRN,"is_revoked":BOOL,
   "expires_at":DT,"created_at":DT}),
 # invites
 "InviteCreate": S({"email":{"type":"string","format":"email"},
   "role":{"$ref":"#/components/schemas/RoleName"},
   "scope":S({"group_ids":{"type":"array","items":UUID},
     "can_take_attendance":BOOL,"can_grade":BOOL,"can_upload_solutions":BOOL,
     "student_id":{**UUID,"nullable":True,"description":"For a PARENT invite: the child to link."}},
     desc="Role-shaped. Assistant invites carry groups and flags; parent invites carry the child.")},
   ["email","role"]),
 "Invite": S({"invite_id":UUID,"email":STR,"role":{"$ref":"#/components/schemas/RoleName"},
   "expires_at":DT,"accepted_at":DTN,"created_at":DT}),
 "InvitePreview": S({"inviter_name":STR,"role":{"$ref":"#/components/schemas/RoleName"},
   "scope_description":{**STR,"description":"Human-readable, e.g. \"attendance, grading, and homework uploads for his classes\" (WF 04)."},
   "expires_at":DT}),
 "InviteAccept": S({"full_name":STR,"password":{"type":"string","format":"password"}},["password"]),
 # billing
 "Plan": S({"plan_id":UUID,"name":STR,"max_students":INT,"price":MONEY,
   "billing_period":E("MONTHLY","ANNUALLY")}),
 "SubscriptionCreate": S({"plan_id":UUID,"payment_token":{**STR,"description":"Opaque token from the payment provider."}},["plan_id"]),
 "SubscriptionUpdate": S({"plan_id":UUID,"status":E("ACTIVE","CANCELLED")}),
 "Subscription": S({"subscription_id":UUID,"plan":{"$ref":"#/components/schemas/Plan"},
   "status":E("ACTIVE","EXPIRED","CANCELLED"),"start_date":DT,"end_date":DT}),
 # curriculum
 "Course": S({"course_id":UUID,"course_code":STR,"subject_name":STR,"description":STRN,
   "grade_level":STRN,"fees":MONEY,"status":{"$ref":"#/components/schemas/CourseStatus"},
   "chapter_count":INT,"group_count":INT}),
 "CourseCreate": S({"course_code":STR,"subject_name":STR,"description":STR,"grade_level":STR,
   "fees":MONEY},["subject_name"]),
 "CourseUpdate": S({"subject_name":STR,"description":STR,"grade_level":STR,"fees":MONEY,
   "status":{"$ref":"#/components/schemas/CourseStatus"}}),
 "Chapter": S({"chapter_id":UUID,"course_id":UUID,"title":STR,"description":STRN,"order_index":INT,
   "lessons":{"type":"array","items":{"$ref":"#/components/schemas/Lesson"},
     "description":"Present only when `include=lessons`."}}),
 "ChapterCreate": S({"title":STR,"description":STR,"order_index":INT},["title"]),
 "ChapterUpdate": S({"title":STR,"description":STR}),
 "Lesson": S({"lesson_id":UUID,"chapter_id":UUID,"title":STR,"description":STRN,"order_index":INT,
   "status":{**E("DRAFT","PUBLISHED"),"description":"Gap G3 — this field does not exist in the ERD yet."},
   "material_count":INT,"recording_count":INT,"assignment_count":INT}),
 "LessonCreate": S({"title":STR,"description":STR,"order_index":INT},["title"]),
 "LessonUpdate": S({"title":STR,"description":STR}),
 # materials
 "Material": S({"material_id":UUID,"lesson_id":UUID,"title":STR,"file_url":STR,
   "access_mode":{"$ref":"#/components/schemas/AccessMode"},
   "size_bytes":{**INT,"nullable":True,"description":"Gap A9 — not stored."},
   "mime_type":{**STRN,"description":"Gap A9 — not stored."},"uploaded_at":DT}),
 "MaterialCreate": S({"title":STR,"file_url":STR,
   "access_mode":{"$ref":"#/components/schemas/AccessMode"}},["title","file_url"]),
 "MaterialUpdate": S({"title":STR,"access_mode":{"$ref":"#/components/schemas/AccessMode"}}),
 "SignedUrl": S({"url":STR,"expires_at":DT,
   "access_mode":{"$ref":"#/components/schemas/AccessMode"}}),
 "Recording": S({"recorded_session_id":UUID,"lesson_id":UUID,"title":STR,"video_url":STR,
   "duration_seconds":INT,"order_index":INT,
   "max_watch_limit":{**INT,"description":"0 means unlimited. Declarative only in this pass."},
   "publish_at":DTN,"deadline":DTN,"recorded_from_live_session_id":{**UUID,"nullable":True},
   "created_at":DT}),
 "RecordingCreate": S({"title":STR,"video_url":STR,"duration_seconds":INT,"order_index":INT,
   "max_watch_limit":INT,"publish_at":DTN,"deadline":DTN,
   "recorded_from_live_session_id":{**UUID,"nullable":True}},["title","video_url"]),
 "RecordingUpdate": S({"title":STR,"max_watch_limit":INT,"publish_at":DTN,"deadline":DTN}),
 "UploadRequest": S({"filename":STR,"mime_type":STR,"size_bytes":INT},["filename","mime_type"]),
 "UploadTarget": S({"upload_url":STR,"file_url":STR,"expires_at":DT},["upload_url","file_url"]),
 # assignments
 "Assignment": S({"assignment_id":UUID,"lesson_id":UUID,"title":STR,"description":STRN,
   "instructions_file_url":STRN,"order_index":INT,"due_date":DT,
   "solution_file_url":STRN,"solution_released_at":DTN,"created_at":DT,
   "submission_count":INT},desc="Curriculum branch. Never scored."),
 "AssignmentCreate": S({"title":STR,"description":STR,"instructions_file_url":STR,
   "due_date":DT,"order_index":INT},["title","due_date"]),
 "AssignmentUpdate": S({"title":STR,"description":STR,"due_date":DT}),
 "SolutionUpload": S({"solution_file_url":STR},["solution_file_url"]),
 "AssignmentSubmissionCreate": S({"file_url":STR,
   "student_note":{**STR,"description":"WF 23's optional \"Notes for your teacher\"."}},["file_url"]),
 "AssignmentSubmission": S({"submission_id":UUID,"assignment_id":UUID,"student_id":UUID,
   "student_name":STR,"file_url":STR,"student_note":STRN,
   "is_late":{**BOOL,"description":"Computed once at submission against `due_date`. Never changes."},
   "submitted_at":DT}),
 # groups
 "Group": S({"group_id":UUID,"course_id":UUID,"group_name":STR,
   "schedule_info":{**STRN,"description":"Default recurrence hint. Not authoritative."},
   "classroom_location":{**STRN,"description":"Default room. Not authoritative."},
   "max_capacity":INT,"student_count":INT}),
 "GroupCreate": S({"group_name":STR,"schedule_info":STR,"classroom_location":STR,
   "max_capacity":INT},["group_name"]),
 "GroupUpdate": S({"group_name":STR,"schedule_info":STR,"classroom_location":STR,"max_capacity":INT}),
 "EnrollRequest": S({"student_ids":{"type":"array","items":UUID}},["student_ids"]),
 "Student": S({"user_id":UUID,"first_name":STR,"last_name":STR,"email":STR,
   "student_code":STRN,"school_name":STRN,"grade_level":STRN}),
 "AssistantPermissions": S({"can_take_attendance":BOOL,"can_grade":BOOL,"can_upload_solutions":BOOL},
   desc="The three checkboxes WF 13 sets at invite time."),
 "Assistant": S({"user_id":UUID,"first_name":STR,"last_name":STR,"email":STR,
   "groups":{"type":"array","items":S({"group_id":UUID,"group_name":STR,
     "can_take_attendance":BOOL,"can_grade":BOOL,"can_upload_solutions":BOOL,
     "is_revoked":BOOL,"assigned_at":DT})},
   "scope_label":{**STR,"description":"Rendered for WF 13, e.g. \"All sections\" or \"Section A only\"."}}),
 "AssistantUpdate": S({"group_ids":{"type":"array","items":UUID},
   "can_take_attendance":BOOL,"can_grade":BOOL,"can_upload_solutions":BOOL}),
}

schemas.update({
 # scheduling
 "LiveSession": S({"live_session_id":UUID,"group_id":UUID,"group_name":STR,
   "lesson_id":{**UUID,"nullable":True,"description":"Nullable on purpose: revision, exam prep and Q&A map to no lesson."},
   "lesson_title":STRN,"title":STR,"mode":{"$ref":"#/components/schemas/SessionMode"},
   "meeting_url":STRN,"classroom_location":STRN,"scheduled_start":DT,"scheduled_end":DT,
   "status":{"$ref":"#/components/schemas/SessionStatus"},"created_at":DT}),
 "LiveSessionCreate": S({"group_id":UUID,"lesson_id":{**UUID,"nullable":True},"title":STR,
   "mode":{"$ref":"#/components/schemas/SessionMode"},
   "meeting_url":{**STR,"description":"Required when mode is ONLINE."},
   "classroom_location":{**STR,"description":"Required when mode is ONSITE."},
   "scheduled_start":DT,"scheduled_end":DT,
   "recurrence":S({"frequency":E("WEEKLY"),"until":DT},
     desc="Gap G10 — recurrence is not modelled. Shape shown for discussion only.")},
   ["group_id","title","mode","scheduled_start","scheduled_end"]),
 "LiveSessionUpdate": S({"title":STR,"mode":{"$ref":"#/components/schemas/SessionMode"},
   "meeting_url":STR,"classroom_location":STR,"scheduled_start":DT,"scheduled_end":DT,
   "lesson_id":{**UUID,"nullable":True},
   "scope":{**E("this","this_and_following"),
     "description":"Gap G10 — only meaningful once recurrence exists (WF 09)."}}),
 "JoinInfo": S({"can_join":BOOL,"opens_at":DT,"meeting_url":STRN,
   "seconds_until_open":{**INT,"nullable":True}}),
 "MeetingWebhook": S({"external_meeting_id":STR,"event":E("participant_joined","participant_left"),
   "participant_email":STR,"occurred_at":DT}),
 # attendance
 "AttendanceRecord": S({"id":UUID,"student_id":UUID,"student_name":STR,"live_session_id":UUID,
   "session_title":STR,"scheduled_start":DT,
   "status":{"$ref":"#/components/schemas/AttendanceStatus"},"recorded_at":DT}),
 "AttendanceSheet": S({"live_session_id":UUID,"session_title":STR,"scheduled_start":DT,
   "records":{"type":"array","items":{"$ref":"#/components/schemas/AttendanceRecord"}}},
   desc="Built from recorded rows unioned with current membership — see the endpoint note."),
 "AttendanceSave": S({"records":{"type":"array","items":S({"student_id":UUID,
   "status":{"$ref":"#/components/schemas/AttendanceStatus"}},["student_id","status"])}},["records"],
   "The full status array for the session. Serves both \"Mark all present\" and \"Save\"."),
 "AttendanceUpdate": S({"status":{"$ref":"#/components/schemas/AttendanceStatus"}},["status"]),
 # quizzes
 "Quiz": S({"quiz_id":UUID,"group_id":UUID,"group_name":STR,
   "lesson_id":{**UUID,"nullable":True,"description":"Tagging only."},"title":STR,"max_score":INT,
   "opens_at":DT,"closes_at":DT,
   "duration_seconds":{**INT,"nullable":True,"description":"Null means untimed."},
   "question_count":INT,"created_at":DT}),
 "QuizDetail": {"allOf":[{"$ref":"#/components/schemas/Quiz"},
   S({"questions":{"type":"array","items":{"$ref":"#/components/schemas/QuizQuestion"}}})]},
 "QuizCreate": S({"title":STR,"lesson_id":{**UUID,"nullable":True},"max_score":INT,
   "opens_at":DT,"closes_at":DT,"duration_seconds":{**INT,"nullable":True}},
   ["title","opens_at","closes_at"]),
 "QuizUpdate": S({"title":STR,"max_score":INT,"opens_at":DT,"closes_at":DT,
   "duration_seconds":{**INT,"nullable":True}}),
 "QuizQuestion": S({"question_id":UUID,"quiz_id":UUID,"question_text":STR,
   "question_type":{"$ref":"#/components/schemas/QuestionType"},
   "options":{"type":"array","items":STR,"nullable":True,"description":"MCQ only."},
   "model_answer":{**STRN,"description":"Never returned to students."},
   "points":{"type":"string"},"order_index":INT}),
 "QuizQuestionCreate": S({"question_text":STR,
   "question_type":{"$ref":"#/components/schemas/QuestionType"},
   "options":{"type":"array","items":STR},"model_answer":STR,"points":{"type":"string"},
   "order_index":INT},["question_text","question_type","points"]),
 "QuizQuestionUpdate": S({"question_text":STR,"options":{"type":"array","items":STR},
   "model_answer":STR,"points":{"type":"string"}}),
 # attempts
 "QuizAttempt": S({"attempt_id":UUID,"quiz_id":UUID,"quiz_title":STR,"student_id":UUID,
   "student_name":STR,"started_at":DT,"expires_at":DT,"submitted_at":DTN,
   "auto_score":SCORE,"total_score":SCORE,"feedback_comments":STRN,
   "status":{"$ref":"#/components/schemas/AttemptStatus"},
   "graded_by_user_id":{**UUID,"nullable":True},"graded_at":DTN,
   "pending_answer_count":{**INT,"description":"Structured answers still awaiting a human."}}),
 "AttemptDetail": S({"attempt_id":UUID,"quiz_id":UUID,"quiz_title":STR,"started_at":DT,
   "expires_at":DT,"seconds_remaining":INT,
   "status":{"$ref":"#/components/schemas/AttemptStatus"},
   "questions":{"type":"array","items":S({"question_id":UUID,"question_text":STR,
     "question_type":{"$ref":"#/components/schemas/QuestionType"},
     "options":{"type":"array","items":STR,"nullable":True},"points":{"type":"string"},
     "order_index":INT,"student_answer":STRN,
     "answered":{**BOOL,"description":"Drives the WF 22 navigator."}})}},
   desc="The in-flight quiz. Model answers are never included."),
 "AnswerSaveRequest": S({"answers":{"type":"array","items":S({"question_id":UUID,
   "student_answer":STR},["question_id","student_answer"])}},["answers"]),
 "AttemptResult": S({"attempt_id":UUID,"quiz_id":UUID,"quiz_title":STR,"submitted_at":DTN,
   "auto_score":{**SCORE,"description":"MCQ subtotal, written at submit and shown immediately."},
   "total_score":{**SCORE,"description":"Null until every structured answer is graded."},
   "max_score":INT,"grading_status":{**E("PENDING","GRADED"),
     "description":"Explicit so the client renders \"pending\" rather than inferring it from a null."},
   "feedback_comments":STRN,
   "answers":{"type":"array","items":S({"question_id":UUID,"question_text":STR,
     "student_answer":STRN,"points_awarded":SCORE,"points_possible":{"type":"string"},
     "evaluator_comment":STRN})}}),
 # grading
 "GradingQueueItem": S({"answer_id":UUID,"attempt_id":UUID,"quiz_id":UUID,"quiz_title":STR,
   "group_id":UUID,"group_name":STR,"student_id":UUID,
   "student_name":{**STR,"description":"WF 15's \"Youssef T.\"."},
   "question_id":UUID,"question_text":STR,
   "question_number":{**INT,"description":"WF 15's \"Q4\"."},
   "points_possible":{**STR,"description":"WF 15's \"2 pts\"."},
   "student_answer":STRN,"model_answer":{**STRN,"description":"Shown to the grader (closes gap B17)."},
   "claimed_by_user_id":{**UUID,"nullable":True},"claimed_at":DTN}),
 "GradingSummary": S({"total_pending":INT,
   "by_quiz":{"type":"array","items":S({"quiz_id":UUID,"quiz_title":STR,"group_name":STR,
     "pending_answers":INT,"attempts_total":INT,
     "attempts_complete":{**INT,"description":"Backs WF 15's \"18/24 already complete\"."}})},
   "by_group":{"type":"array","items":S({"group_id":UUID,"group_name":STR,"pending_answers":INT})}}),
 "GradeAnswerRequest": S({"points_awarded":{**STR,"description":"Decimal string. Must be between 0 and the question's points."},
   "evaluator_comment":STR},["points_awarded"]),
 "QuizAnswer": S({"answer_id":UUID,"attempt_id":UUID,"question_id":UUID,"student_answer":STRN,
   "points_awarded":SCORE,"evaluator_comment":STRN,
   "graded_by_user_id":{**UUID,"nullable":True,
     "description":"Null on a scored answer means the machine graded it — MCQs are auto-scored."},
   "graded_at":DTN}),
 "BulkGradeRequest": S({"grades":{"type":"array","items":S({"answer_id":UUID,
   "points_awarded":STR,"evaluator_comment":STR},["answer_id","points_awarded"])}},["grades"]),
 "BulkGradeResult": S({"graded":INT,"failed":INT,
   "results":{"type":"array","items":S({"answer_id":UUID,"ok":BOOL,"error_code":STRN})}},
   desc="Partial success is reported per item rather than failing the whole batch."),
 # roster & dashboards
 "StudentRosterRow": S({"student_id":UUID,"name":STR,
   "section":{**STR,"description":"Assumes one group per course per student (gaps C13, D4)."},
   "attendance_percent":{**INT,"nullable":True},
   "last_quiz_percent":{**INT,"nullable":True},
   "homework_status":E("submitted","late","missing")}),
 "StudentDetail": S({"student":{"$ref":"#/components/schemas/Student"},
   "groups":{"type":"array","items":{"$ref":"#/components/schemas/Group"}},
   "attendance_percent":{**INT,"nullable":True},"average_grade":{**INT,"nullable":True},
   "parents":{"type":"array","items":S({"user_id":UUID,"name":STR,"email":STR,"phone":STRN}),
     "description":"May contain several — PARENT_STUDENTS is many-to-many (gap D33)."}}),
 "InstructorDashboard": S({"stats":{"type":"array","items":S({"key":STR,"label":STR,"value":INT,
   "deep_link":STR}),"description":"Gap C3 — the wireframe's four labels are blank placeholders."},
   "todays_sessions":{"type":"array","items":{"$ref":"#/components/schemas/LiveSession"}},
   "pending_grading":{"$ref":"#/components/schemas/GradingSummary"}}),
 "AssistantDashboard": S({"assigned_groups":{"type":"array","items":{"$ref":"#/components/schemas/Group"}},
   "pending_grading":{"$ref":"#/components/schemas/GradingSummary"},
   "todays_sessions":{"type":"array","items":{"$ref":"#/components/schemas/LiveSession"},
     "description":"Gap C15 — TAs are assigned to groups, not sessions."}}),
 "StudentDashboard": S({"next_session":{"allOf":[{"$ref":"#/components/schemas/LiveSession"}],"nullable":True},
   "join":{"$ref":"#/components/schemas/JoinInfo"},
   "due_soon":{"type":"array","items":S({"kind":E("assignment","quiz"),"id":UUID,"title":STR,"due_at":DT})},
   "recent_grades":{"type":"array","items":{"$ref":"#/components/schemas/AttemptResult"}}}),
 "ParentDashboard": S({"children":{"type":"array","items":{"$ref":"#/components/schemas/ChildSummary"}},
   "recent_updates":{"type":"array","items":{"$ref":"#/components/schemas/Notification"}}}),
 # fees
 "FeeSummary": S({"this_month":MONEY,"outstanding":MONEY,"paid_on_time_percent":INT}),
 "Fee": S({"fee_id":UUID,"student_id":UUID,"student_name":STR,"group_id":UUID,"section":STR,
   "plan":{**STR,"description":"WF 12's \"Monthly\" column. Cadence is undecided (gap D19)."},
   "period_start":DT,"period_end":DT,"amount":MONEY,"status":E("PAID","DUE","OVERDUE"),
   "paid_at":DTN}),
 "Receipt": S({"receipt_id":UUID,"fee_id":UUID,"amount":MONEY,"paid_at":DT,"document_url":STR}),
 "PaymentCreate": S({"fee_id":UUID,"payment_token":STR},["fee_id","payment_token"]),
 "Payment": S({"payment_id":UUID,"fee_id":UUID,"amount":MONEY,"paid_at":DT,
   "status":E("SUCCEEDED","FAILED")}),
 # parent
 "ChildSummary": S({"student_id":UUID,"name":STR,
   "course_label":{**STR,"description":"WF 17's \"IG Physics\". No curriculum field exists (gap C12)."},
   "attendance_percent":{**INT,"nullable":True},"average_grade":{**INT,"nullable":True},
   "fee_status":{**E("PAID","DUE","OVERDUE"),"nullable":True,"description":"Gap G2."}}),
 "ChildDetail": S({"student":{"$ref":"#/components/schemas/Student"},
   "courses":{"type":"array","items":{"$ref":"#/components/schemas/EnrolledCourse"}},
   "attendance_percent":{**INT,"nullable":True},"average_grade":{**INT,"nullable":True}}),
 # notifications
 "Notification": S({"notification_id":UUID,"title":STR,"message":STR,
   "type":E("ASSIGNMENT","QUIZ","ANNOUNCEMENT","SYSTEM"),"is_read":BOOL,"created_at":DT,
   "target_type":{**STRN,"description":"Gap A23 — no target reference exists, so deep-linking is unavailable."},
   "target_id":{**UUID,"nullable":True,"description":"Gap A23."}}),
 "MarkReadRequest": S({"notification_ids":{"type":"array","items":UUID},
   "all":{**BOOL,"default":False,"description":"Mark every unread notification read."}}),
 "EventStream": S({"type":{**STR,"description":"e.g. `attendance.saved`, `quiz.graded`."},
   "payload":{"type":"object"},"occurred_at":DT},
   desc="One SSE frame. The response content type is `text/event-stream`."),
 # student portal
 "EnrolledCourse": S({"course_id":UUID,"subject_name":STR,"group_id":UUID,"group_name":STR,
   "teacher_name":STR}),
 "LessonProgress": S({"lesson_id":UUID,"chapter_title":STR,"title":STR,"order_index":INT,
   "progress":{**E("DONE","IN_PROGRESS","NOT_STARTED"),"description":"Gap G8 — no progress data exists."},
   "materials":{"type":"array","items":{"$ref":"#/components/schemas/Material"}},
   "recordings":{"type":"array","items":{"$ref":"#/components/schemas/Recording"}}}),
 "StudentAssignment": S({"assignment_id":UUID,"title":STR,"lesson_title":STR,"course_name":STR,
   "due_date":DT,"submitted":BOOL,"is_late":{**BOOL,"nullable":True},
   "solution_available":{**BOOL,"description":"True once `solution_released_at` has passed."}}),
 "StudentQuiz": S({"quiz_id":UUID,"title":STR,"course_name":STR,"opens_at":DT,"closes_at":DT,
   "duration_seconds":{**INT,"nullable":True},"attempt_status":{
     **E("NOT_STARTED","IN_PROGRESS","SUBMITTED","GRADED"),"description":"Derived from the caller's attempt."}}),
})

RESP = {c: {"description": d, "content": {"application/json":
        {"schema": {"$ref": "#/components/schemas/Error"}}}} for c, d in {
 "400":"Malformed request body or parameters.",
 "401":"Missing, invalid or expired access token.",
 "403":"Authenticated, but the caller lacks the required role, ownership scope or permission flag (`INSUFFICIENT_SCOPE`).",
 "404":"No such resource, or the caller may not see it.",
 "409":"Conflict with current state — a uniqueness constraint, a lock, or a RESTRICT delete rule.",
 "410":"The token has expired or was already used.",
 "422":"Well-formed but violates a schema invariant. See the error catalog.",
}.items()}

TAGS = [
 ("Authentication","Login, token rotation, sign-up, password reset and profile."),
 ("Invites","Instructor-issued invites — the only route to a TA, student or parent account."),
 ("Billing","Instructor → platform subscriptions. Distinct from student fees."),
 ("Courses","The curriculum root."),
 ("Chapters","Chapters within a course."),
 ("Lessons","Lessons within a chapter, and publish state."),
 ("Materials","Files attached to a lesson."),
 ("Recordings","On-demand video attached to a lesson."),
 ("Uploads","Signed upload targets. Transport only."),
 ("Assignments","Homework — curriculum branch, checked for on-time submission, never scored."),
 ("Groups","Cohorts, called \"sections\" in the wireframes."),
 ("Assistants","TA scope and the three permission flags."),
 ("Scheduling","Live sessions, onsite and online."),
 ("Attendance","Recorded against a live session, never against a lesson."),
 ("Quizzes","Timed assessments — cohort branch, issued to one group."),
 ("Quiz attempts","The student-side attempt lifecycle."),
 ("Grading","The TA grading queue for structured answers."),
 ("Roster","Students and their computed aggregates."),
 ("Dashboards","Per-role landing screens."),
 ("Fees","Student → instructor payments."),
 ("Parent portal","Read-only views of linked children."),
 ("Notifications","The in-app feed."),
 ("Events","Server-Sent Events — the real-time transport."),
 ("Student portal","Enrollment-scoped reads."),
]

spec = {
 "openapi": "3.1.0",
 "info": {
   "title": "Montu E-Learning Platform API",
   "version": "0.1.0-draft",
   "description":
     "REST API for the Montu e-learning platform — a centralized LMS for independent IGCSE and "
     "American-Diploma instructors, serving four linked tiers: instructor, teaching assistant, "
     "parent and student.\n\n"
     "**This is a specification, not a description of running code.** The backend is scaffolding "
     "only. Every endpoint is derived from the entity-relationship diagram and the 24-screen "
     "wireframe set, and each one carries a status line saying whether it is fully backed by the "
     "schema, depends on an open decision, or is blocked on a missing entity.\n\n"
     "Read the *Concepts* section first — the path conventions, the role and ownership model, the "
     "two-branch rule and the error catalog apply to every operation and are not repeated per "
     "endpoint.",
   "contact": {"name": "Montu Tech"},
 },
 "servers": [
   {"url": "https://api.montu.example/api/v1", "description": "Production (not yet deployed)"},
   {"url": "http://localhost:3000/api/v1", "description": "Local development"},
 ],
 "security": [{"bearerAuth": []}],
 "tags": [{"name": n, "description": d} for n, d in TAGS],
 "paths": dict(paths),
 "components": {
   "securitySchemes": {"bearerAuth": {"type":"http","scheme":"bearer","bearerFormat":"JWT",
     "description":"Access token from `POST /auth/login` or `POST /auth/refresh`."}},
   "schemas": schemas,
   "responses": RESP,
 },
}

def fix_nullable(node):
    """OpenAPI 3.1 removed `nullable: true` — express it as a type union instead."""
    if isinstance(node, dict):
        if node.pop("nullable", None) is True:
            t = node.get("type")
            if isinstance(t, str):        node["type"] = [t, "null"]
            elif isinstance(t, list):
                if "null" not in t:       node["type"] = t + ["null"]
            elif "allOf" in node:
                node["oneOf"] = node.pop("allOf") + [{"type": "null"}]
            else:                         node["type"] = ["null"]
        for v in node.values(): fix_nullable(v)
    elif isinstance(node, list):
        for v in node: fix_nullable(v)
    return node

fix_nullable(spec)

class Dumper(yaml.SafeDumper): pass
def str_presenter(d, x):
    if "\n" in x: return d.represent_scalar("tag:yaml.org,2002:str", x, style="|")
    return d.represent_scalar("tag:yaml.org,2002:str", x)
Dumper.add_representer(str, str_presenter)

out = "/home/elhussienawad/Montu/Elearn-backend/docs/api/openapi.yaml"
with open(out,"w") as f:
    f.write("# Generated for GitBook. Source of truth: docs/erd.md + docs/api-resource-map.md\n")
    yaml.dump(spec, f, Dumper=Dumper, sort_keys=False, allow_unicode=True, width=100)

ops = sum(len(v) for v in paths.values())
print(f"paths: {len(paths)}  operations: {ops}  schemas: {len(schemas)}")
