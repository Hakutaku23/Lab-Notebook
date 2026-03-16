<template>
  <div class="shell">
    <header class="app-header">
      <div>
        <h1>电子实验记录本</h1>
        <p class="muted">第四步：模板管理 / 记录编辑 / 附件上传 / 版本快照</p>
      </div>

      <nav class="nav">
        <RouterLink class="nav-link" to="/projects">项目</RouterLink>
        <RouterLink class="nav-link" to="/templates">模板管理</RouterLink>
        <RouterLink class="nav-link" to="/records">记录列表</RouterLink>
        <RouterLink class="nav-link" to="/records/new">新建记录</RouterLink>
      </nav>
    </header>

    <main>
      <RouterView />
    </main>
  </div>
</template>