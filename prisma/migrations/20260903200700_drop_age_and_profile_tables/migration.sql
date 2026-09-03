-- Drop profile tables added for GET/PATCH /me/profile (rolled back for now).
DROP TABLE IF EXISTS "teacher_subjects";
DROP TABLE IF EXISTS "teachers";
DROP TABLE IF EXISTS "students";
DROP TABLE IF EXISTS "parents";
DROP TABLE IF EXISTS "subjects";
DROP TYPE IF EXISTS "TeacherCurriculum";
DROP TYPE IF EXISTS "CourseCurriculum";

-- Age was never used by any screen or API field.
ALTER TABLE "users" DROP COLUMN IF EXISTS "age";
