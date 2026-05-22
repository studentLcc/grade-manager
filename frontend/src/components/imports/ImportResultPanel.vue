<script setup lang="ts">
import { computed } from 'vue'
import type { StudentImportResult } from '../../api/students'

const props = defineProps<{
  result: StudentImportResult | null
}>()

const importStatusLabels: Record<string, string> = {
  pending: '待处理',
  processing: '处理中',
  success: '成功',
  partial_success: '部分成功',
  failed: '失败',
}

const detailPath = computed(() => (props.result ? `/imports/${props.result.batch_id}` : ''))
const statusLabel = computed(() => (props.result ? importStatusLabels[props.result.status] || '未知状态' : ''))
</script>

<template>
  <section v-if="result" class="gm-import-result" aria-label="导入结果">
    <div>
      <span>导入状态</span>
      <strong>{{ statusLabel }}</strong>
    </div>
    <div>
      <span>成功</span>
      <strong>{{ result.success_count }}</strong>
    </div>
    <div>
      <span>失败</span>
      <strong>{{ result.failed_count }}</strong>
    </div>
    <RouterLink class="gm-import-link" :to="detailPath">查看导入详情</RouterLink>
  </section>
</template>
