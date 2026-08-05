// Derives a display name/initials from whatever we actually have.
//
// The API gives us the full name (first_name/last_name) only from
// POST /api/auth/register's UserResponse. POST /api/auth/login returns only
// {access_token}, no user object — there's no /api/auth/me to fall back on.
// So after a plain login (no register in this session), the only
// user-identifying thing the frontend has is the email the person typed into
// the login form. We store whatever's available and degrade gracefully:
// full name when we have it (post-register), otherwise something derived
// from the email (post-login).
export function getDisplayName(user) {
  if (!user) return "";
  if (user.first_name) return `${user.first_name} ${user.last_name ?? ""}`.trim();
  if (user.email) return user.email.split("@")[0];
  return "";
}

export function getInitials(user) {
  if (!user) return "?";
  if (user.first_name) {
    return `${user.first_name[0]}${user.last_name?.[0] ?? ""}`.toUpperCase();
  }
  if (user.email) {
    const local = user.email.split("@")[0];
    const parts = local.split(/[._-]/).filter(Boolean);
    if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase();
    return local.slice(0, 2).toUpperCase();
  }
  return "?";
}
