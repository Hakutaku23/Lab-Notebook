export const USER_ROLE_LABELS: Record<string, string> = {
  admin: "管理员",
  researcher: "研究人员",
  member: "普通成员",
};

export function getUserRoleLabel(role?: string | null): string {
  if (!role) {
    return "普通成员";
  }

  return USER_ROLE_LABELS[role] ?? role;
}
