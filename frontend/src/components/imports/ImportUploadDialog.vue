<script setup lang="ts">
import { computed } from 'vue'
import type { UploadRequestOptions } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'

const props = withDefaults(
  defineProps<{
    modelValue: boolean
    title: string
    contextLabel: string
    contextValue: string
    contextWarning?: boolean
    optionValue?: boolean
    optionLabel?: string
    downloadLabel?: string
    downloadDisabled?: boolean
    optionDisabled?: boolean
    uploadDisabled?: boolean
    uploading?: boolean
    uploadIdleText: string
    uploadLoadingText?: string
    uploadHint?: string
    accept?: string
    name?: string
    width?: string
    httpRequest: (options: UploadRequestOptions) => unknown
  }>(),
  {
    accept: '.xlsx,.xlsm',
    downloadLabel: '下载模板',
    name: 'file',
    optionLabel: '',
    uploadHint: '或点击选择 .xlsx / .xlsm 文件',
    uploadLoadingText: '上传中',
    width: '680px',
  },
)

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'update:optionValue': [value: boolean]
  download: []
}>()

const visible = computed({
  get: () => props.modelValue,
  set: (value: boolean) => emit('update:modelValue', value),
})

const optionModel = computed<boolean>({
  get: () => props.optionValue ?? false,
  set: (value) => emit('update:optionValue', value),
})
</script>

<template>
  <el-dialog v-model="visible" :title="title" :width="width">
    <div class="gm-import-actions">
      <el-button :disabled="downloadDisabled" @click="emit('download')">{{ downloadLabel }}</el-button>
      <el-checkbox v-if="optionLabel" v-model="optionModel" :disabled="optionDisabled">{{ optionLabel }}</el-checkbox>
    </div>

    <div class="gm-import-dialog-context" :class="{ 'is-warning': contextWarning }">
      <span>{{ contextLabel }}</span>
      <strong>{{ contextValue }}</strong>
    </div>

    <el-upload
      drag
      :http-request="httpRequest"
      :disabled="uploadDisabled"
      :show-file-list="false"
      :accept="accept"
      :name="name"
    >
      <div class="gm-upload-dropzone">
        <el-icon class="gm-upload-icon"><UploadFilled /></el-icon>
        <strong>{{ uploading ? uploadLoadingText : uploadIdleText }}</strong>
        <span>{{ uploadHint }}</span>
      </div>
    </el-upload>

    <slot />
  </el-dialog>
</template>
