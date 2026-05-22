<template>
  <section class="gm-dashboard">
    <div class="gm-page-header">
      <div>
        <h1>工作台</h1>
        <p>查看近期考试、待录入成绩和班级概览。</p>
      </div>
      <el-button type="primary">新建考试</el-button>
    </div>

    <div class="gm-metrics">
      <article class="gm-card">
        <span>班级</span>
        <strong>0</strong>
      </article>
      <article class="gm-card">
        <span>学生</span>
        <strong>0</strong>
      </article>
      <article class="gm-card">
        <span>进行中考试</span>
        <strong>0</strong>
      </article>
      <article class="gm-card">
        <span>待处理导入</span>
        <strong>0</strong>
      </article>
    </div>

    <div class="gm-content-grid">
      <section class="gm-page-card">
        <h2>近期考试</h2>
        <p>后续任务将接入考试列表和成绩录入入口。</p>
      </section>
      <section class="gm-page-card">
        <h2>班级动态</h2>
        <p>后续任务将展示班级、课程和导入状态。</p>
      </section>
    </div>
  </section>
</template>
