# Conventions

Rules that hold for every endpoint. They are stated once here rather than repeated in each
operation.

## Paths nest one level, then go flat

A collection is nested under the parent that owns it. An individual item is addressed flat, by its
own id.

```http
GET   /api/v1/courses/{courseId}/chapters      # collection, scoped by owner
POST  /api/v1/courses/{courseId}/chapters      # create inside owner
GET   /api/v1/chapters/{chapterId}             # item, flat
PATCH /api/v1/chapters/{chapterId}             # item, flat
```

This keeps paths from growing into
`/courses/{}/chapters/{}/lessons/{}/materials/{}` while still expressing ownership where it
matters. Note the consequence for lessons: a lesson is created at
`POST /chapters/{chapterId}/lessons`, because `LESSONS.chapter_id` is the foreign key. A lesson has
no direct course parent — the course is derived through the chapter.

## Casing

Paths are `kebab-case`; JSON fields are `snake_case`, mirroring the database column names
(`course_id`, `order_index`, `scheduled_start`).

## Identifiers, timestamps and money

| Kind | Format | Note |
|---|---|---|
| Resource ids | UUID v4 string | `"9f2a1c4e-..."` |
| Timestamps | ISO-8601 with `Z` | **Always UTC.** Rendering in the viewer's timezone is a client concern |
| Money | Decimal as string | `"250.00"` — avoids float loss. Single implied currency |
| Scores | Decimal as string | Same reason |

## Reordering is a bulk `PUT` on the collection

Every ordered collection — chapters, lessons, recordings, assignments, quiz questions — is
reordered by sending the complete ordered array of ids to a `/order` sub-resource:

```http
PUT /api/v1/courses/{courseId}/chapters/order

{ "order": ["9f2a1c4e-...", "3b7d0a11-...", "c81e4f92-..."] }
```

This is not a stylistic choice. `UNIQUE (course_id, order_index)` and its siblings mean that moving
items one at a time produces transient collisions mid-sequence. The bulk `PUT` reassigns the whole
sequence in one transaction, and one drag-and-drop is one request.

## Bulk writes are first class

Reordering is not the only one. "Mark all present" is a single `PUT` carrying the full attendance
array; grading takes a bulk array; enrollment takes an array of student ids. The primary instructor
persona manages 150+ students across multiple sections, so per-item loops are the wrong shape
throughout.

## List envelope

Every collection response uses the same envelope, with cursor pagination:

```json
{
  "data": [],
  "page": {
    "limit": 25,
    "cursor": null,
    "next_cursor": "eyJpZCI6...",
    "total": 158
  }
}
```

`limit` defaults to 25 and caps at 100. Pass `cursor` from the previous response's `next_cursor` to
continue.

## Derived values are computed on read

Attendance percentages, average grades, pending-grading counts, revenue aggregates and lesson
progress are **never stored**. They are computed per request. This means they are always current
and never need a backfill, and it means they cannot be filtered on cheaply — the filters that exist
on [`GET /students`](../reference/roster.md) are the supported ones.
