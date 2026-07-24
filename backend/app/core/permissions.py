"""Static RBAC definition: User -> Role -> Permission -> Allowed Action.

Roles and permissions are seeded into the database (see app/db/seed.py) so
they can be inspected/extended at runtime, but the canonical definition of
"what exists" lives here in code, matching the spec's four built-in roles.
"""

# Permission codes -----------------------------------------------------------
MANAGE_USERS = "users:manage"
VIEW_USERS = "users:view"
MANAGE_ROLES = "roles:manage"
VIEW_ALL_SECURITY_DATA = "security:view_all"
MANAGE_ALERTS = "alerts:manage"
VIEW_LOGS = "logs:view"
INVESTIGATE_THREATS = "threats:investigate"
MANAGE_INCIDENTS = "incidents:manage"
VIEW_REPORTS = "reports:view"
REVIEW_COMPLIANCE = "compliance:review"
ACCESS_APP = "app:access"
VIEW_ANALYTICS = "analytics:view"

ALL_PERMISSIONS: dict[str, str] = {
    MANAGE_USERS: "Create, edit, delete users and reset passwords",
    VIEW_USERS: "View user list and profiles",
    MANAGE_ROLES: "Assign roles and permissions",
    VIEW_ALL_SECURITY_DATA: "View all security data across the platform",
    MANAGE_ALERTS: "Create, update, and resolve security alerts",
    VIEW_LOGS: "View audit logs and login history",
    INVESTIGATE_THREATS: "Investigate detected threats",
    MANAGE_INCIDENTS: "Manage and resolve security incidents",
    VIEW_REPORTS: "View compliance and analytics reports",
    REVIEW_COMPLIANCE: "Review compliance activity",
    ACCESS_APP: "Access standard application features",
    VIEW_ANALYTICS: "View analytics dashboards",
}

ROLE_ADMIN = "admin"
ROLE_ANALYST = "security_analyst"
ROLE_AUDITOR = "auditor"
ROLE_USER = "user"

ROLE_PERMISSIONS: dict[str, list[str]] = {
    ROLE_ADMIN: [
        MANAGE_USERS,
        VIEW_USERS,
        MANAGE_ROLES,
        VIEW_ALL_SECURITY_DATA,
        MANAGE_ALERTS,
        VIEW_LOGS,
        INVESTIGATE_THREATS,
        MANAGE_INCIDENTS,
        VIEW_REPORTS,
        REVIEW_COMPLIANCE,
        ACCESS_APP,
        VIEW_ANALYTICS,
    ],
    ROLE_ANALYST: [
        VIEW_USERS,
        VIEW_LOGS,
        INVESTIGATE_THREATS,
        MANAGE_INCIDENTS,
        MANAGE_ALERTS,
        VIEW_ANALYTICS,
        ACCESS_APP,
    ],
    ROLE_AUDITOR: [
        VIEW_REPORTS,
        REVIEW_COMPLIANCE,
        VIEW_LOGS,
        VIEW_ANALYTICS,
        ACCESS_APP,
    ],
    ROLE_USER: [
        ACCESS_APP,
    ],
}

ROLE_DESCRIPTIONS: dict[str, str] = {
    ROLE_ADMIN: "Manages users, permissions, and all security data",
    ROLE_ANALYST: "Investigates threats, manages incidents and alerts",
    ROLE_AUDITOR: "Reviews compliance activity and reports",
    ROLE_USER: "Standard application access",
}
