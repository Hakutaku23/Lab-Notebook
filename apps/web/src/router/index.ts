import { createRouter, createWebHistory } from "vue-router";

import ProjectsView from "../views/ProjectsView.vue";
import RecordsView from "../views/RecordsView.vue";
import RecordCreateView from "../views/RecordCreateView.vue";
import RecordDetailView from "../views/RecordDetailView.vue";
import RecordEditView from "../views/RecordEditView.vue";
import TemplatesView from "../views/TemplatesView.vue";
import LoginView from "../views/LoginView.vue";
import AuditLogsView from "../views/AuditLogsView.vue";
import SettingsView from "../views/SettingsView.vue";

import { pinia } from "../stores";
import { useAuthStore } from "../stores/auth";

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: "/",
      redirect: "/projects",
    },
    {
      path: "/login",
      name: "login",
      component: LoginView,
      meta: {
        guestOnly: true,
      },
    },
    {
      path: "/projects",
      name: "projects",
      component: ProjectsView,
      meta: {
        requiresAuth: true,
      },
    },
    {
      path: "/templates",
      name: "templates",
      component: TemplatesView,
      meta: {
        requiresAuth: true,
      },
    },
    {
      path: "/records",
      name: "records",
      component: RecordsView,
      meta: {
        requiresAuth: true,
      },
    },
    {
      path: "/records/new",
      name: "record-create",
      component: RecordCreateView,
      meta: {
        requiresAuth: true,
      },
    },
    {
      path: "/records/:id",
      name: "record-detail",
      component: RecordDetailView,
      meta: {
        requiresAuth: true,
      },
    },
    {
      path: "/records/:id/edit",
      name: "record-edit",
      component: RecordEditView,
      meta: {
        requiresAuth: true,
      },
    },
    {
      path: "/audit-logs",
      name: "audit-logs",
      component: AuditLogsView,
      meta: {
        requiresAuth: true,
        adminOnly: true,
      },
    },
    {
      path: "/settings",
      name: "settings",
      component: SettingsView,
      meta: {
        requiresAuth: true,
      },
    },
  ],
});

router.beforeEach(async (to) => {
  const authStore = useAuthStore(pinia);

  if (!authStore.ready) {
    void authStore.restoreSession();
  }

  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    return {
      path: "/login",
      query: {
        redirect: to.fullPath,
      },
    };
  }

  if (to.meta.adminOnly && !authStore.isAdmin) {
    return {
      name: "projects",
    };
  }

  if (to.meta.guestOnly && authStore.isAuthenticated) {
    const redirect =
      typeof to.query.redirect === "string" && to.query.redirect
        ? to.query.redirect
        : "/projects";

    return redirect;
  }

  return true;
});
