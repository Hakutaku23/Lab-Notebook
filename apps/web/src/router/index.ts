import { createRouter, createWebHistory } from "vue-router";

import ProjectsView from "../views/ProjectsView.vue";
import RecordsView from "../views/RecordsView.vue";
import RecordCreateView from "../views/RecordCreateView.vue";
import RecordDetailView from "../views/RecordDetailView.vue";
import RecordEditView from "../views/RecordEditView.vue";
import TemplatesView from "../views/TemplatesView.vue";

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: "/",
      redirect: "/projects",
    },
    {
      path: "/projects",
      name: "projects",
      component: ProjectsView,
    },
    {
      path: "/templates",
      name: "templates",
      component: TemplatesView,
    },
    {
      path: "/records",
      name: "records",
      component: RecordsView,
    },
    {
      path: "/records/new",
      name: "record-create",
      component: RecordCreateView,
    },
    {
      path: "/records/:id",
      name: "record-detail",
      component: RecordDetailView,
    },
    {
      path: "/records/:id/edit",
      name: "record-edit",
      component: RecordEditView,
    },
  ],
});