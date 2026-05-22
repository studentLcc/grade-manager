<script setup lang="ts">
import type { ImportErrorRecord } from '../../api/imports'

defineProps<{
  errors: ImportErrorRecord[]
}>()
</script>

<template>
  <el-table :data="errors" empty-text="暂无行级错误">
    <el-table-column prop="row_number" label="行号" width="90" />
    <el-table-column prop="field" label="字段" min-width="130" />
    <el-table-column prop="raw_value" label="原始值" min-width="160" />
    <el-table-column prop="reason" label="失败原因" min-width="220" />
  </el-table>
</template>
