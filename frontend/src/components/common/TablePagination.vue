<template>
  <el-pagination
    v-model:current-page="currentPage"
    v-model:page-size="pageSize"
    class="gm-table-pagination-control"
    small
    :pager-count="5"
    layout="prev, pager, next, sizes"
    :page-sizes="[10, 20, 50, 100]"
    :total="total"
    @change="handleChange"
  />
</template>

<script setup lang="ts">
defineProps<{
  total: number
}>()

const currentPage = defineModel<number>('currentPage', { required: true })
const pageSize = defineModel<number>('pageSize', { required: true })

const emit = defineEmits<{
  change: [currentPage: number, pageSize: number]
}>()

function handleChange(nextPage: number, nextPageSize: number) {
  emit('change', nextPage, nextPageSize)
}
</script>
