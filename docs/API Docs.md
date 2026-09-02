## 07 - Course & Curriculum Dashboard

## Get Courses

## Courses

## Headers

## Response

```
200
{
"Course":{
"course_name":"course1",
"course_id":"fn1o380d"
}
}
400
{
"error": "Invalid request"
}
```


## Get Chapters Related to a Course

GET /api/chapters/{course-id}

Fetch chapters related to the course opened in full view

## Headers

## Response

200

```
{
"chapters": [
{
"chapter_title": "chapter1",
"chapter_id": "nodbuo1b31",
"lessons": [
{
"lesson_id": "024nfu024",
"lesson_title": "lesson1",
"lesson_status": "Published"
}
]
}
]
}
```


## Create a new Course

<Description of the endpoint>

## Headers

## Body

## Response


```
200
{
"id": "non231nrn",
"message": "course created successfully"
}
```

## Create a new chapter

Creates a new chapter for a course for the instructor

## Headers

## Body


## Response

```
200
{
"message": "successfully created chapter"
}
```

## Creates lesson

POST/api/lessons/{course-id}

<Description of the endpoint>

## Headers

## Body


| Name | Type | Description |
| --- | --- | --- |
| name | string | Name of the user |
| status |   | status of the lesson |
|   | string |   |
|   |   | enum (Published, Draft) |
|   |   | id of the course related to |
| course-id | string |   |
|   |   | that lesson |

## Response

```
200
{
"lesson-id":"12380147fwrfn",
"message": "succesfully created chapter"
}
```

## Update Chapter

PATCH /api/chapters/{chapter-id}

<Description of the endpoint>

## Headers


## Body

## Response

## Deletes a Course

Deletes a courses belgoning to the instructor

## Headers


## Response

## Deletes a Chapter

Deletes a courses belgoning to the instructor

## Headers

## Response


```
200
{
"message":"chapter deleted successfully"
}
```

## Deletes a lesson

DELETE

Deletes a lessons belgoning to a course

/api/lessons/{lesson-id}

## Headers

## Response

```
200
{
"message":"lesson deleted successfully"
}
```
