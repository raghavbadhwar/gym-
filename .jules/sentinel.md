## 2024-03-04 - [Missing Password Strength Validation in Auth Registration]
**Vulnerability:** Password strength validation logic existed in shared-auth and local auth services, but was entirely bypassed during the user registration endpoints (`/auth/register`) in `CredVerseRecruiter` and `CredVerseIssuer`. This allowed arbitrary weak passwords (e.g. 1 character) to be accepted.
**Learning:** Security validation functions must be strictly enforced at the API boundary, not just exist in utility modules. Shared libraries must be consistently used.
**Prevention:** Introduce a middleware or validation schema (e.g., zod) on the endpoint payload before proceeding to database writes to ensure business and security constraints are globally enforced across subprojects.
