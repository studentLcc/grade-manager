<script setup lang="ts">
import type { FormRules } from 'element-plus'

interface ExamBasicForm {
  name: string
  exam_type: string
  term: string
  remark: string
}

const props = defineProps<{
  modelValue: ExamBasicForm
}>()

const emit = defineEmits<{
  'update:modelValue': [value: ExamBasicForm]
}>()

const examTypeOptions = [
  { label: '校级考试', value: 'school' },
  { label: '单元测验', value: 'quiz' },
  { label: '期中考试', value: 'midterm' },
  { label: '期末考试', value: 'final' },
]

function requiredTrimmed(message: string) {
  return {
    validator: (_rule: unknown, value: string, callback: (error?: Error) => void) => {
      if (!value?.trim()) callback(new Error(message))
      else callback()
    },
    trigger: 'blur',
  }
}

const rules: FormRules = {
  name: [requiredTrimmed('请输入考试名称')],
}

function updateField(field: keyof ExamBasicForm, value: string) {
  emit('update:modelValue', { ...props.modelValue, [field]: value })
}
</script>

<template>
  <el-form :model="modelValue" :rules="rules" label-width="88px">
    <el-form-item label="考试名称" prop="name" required>
      <el-input :model-value="modelValue.name" placeholder="例如：七年级期中考试" @update:model-value="updateField('name', $event)" />
    </el-form-item>
    <div class="gm-form-split">
      <el-form-item label="考试类型">
        <el-select :model-value="modelValue.exam_type" placeholder="选择类型" clearable @update:model-value="updateField('exam_type', $event || '')">
          <el-option v-for="item in examTypeOptions" :key="item.value" :label="item.label" :value="item.value" />
        </el-select>
      </el-form-item>
      <el-form-item label="学期">
        <el-input :model-value="modelValue.term" placeholder="2026-2027-1" @update:model-value="updateField('term', $event)" />
      </el-form-item>
    </div>
    <el-form-item label="备注">
      <el-input :model-value="modelValue.remark" type="textarea" :rows="3" @update:model-value="updateField('remark', $event)" />
    </el-form-item>
  </el-form>
</template>
