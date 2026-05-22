<script setup lang="ts">
import type { ClassRecord } from '../../api/classes'

const props = defineProps<{
  modelValue: number[]
  classes: ClassRecord[]
}>()

const emit = defineEmits<{
  'update:modelValue': [value: number[]]
}>()

function toggleClass(classId: number, selected: boolean) {
  const next = selected ? [...new Set([...props.modelValue, classId])] : props.modelValue.filter((id) => id !== classId)
  emit('update:modelValue', next)
}
</script>

<template>
  <section>
    <div class="gm-selection-grid">
      <label v-for="classRecord in classes" :key="classRecord.id" class="gm-check-card">
        <el-checkbox :model-value="modelValue.includes(classRecord.id)" @change="toggleClass(classRecord.id, Boolean($event))" />
        <span>
          <strong>{{ classRecord.name }}</strong>
          <small>{{ classRecord.grade || '未设置年级' }} · {{ classRecord.academic_year || '未设置学年' }}</small>
        </span>
      </label>
    </div>
    <el-empty v-if="classes.length === 0" description="暂无可选班级" />
  </section>
</template>
