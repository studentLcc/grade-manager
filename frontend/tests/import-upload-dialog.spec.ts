import { describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import ImportUploadDialog from '../src/components/imports/ImportUploadDialog.vue'

const dialogStub = {
  props: ['modelValue', 'title', 'width'],
  template: '<section class="dialog-stub"><h1>{{ title }}</h1><slot /></section>',
}
const buttonStub = { props: ['disabled'], template: '<button :disabled="disabled"><slot /></button>' }
const checkboxStub = {
  props: ['modelValue', 'disabled'],
  emits: ['update:modelValue'],
  template:
    '<label class="checkbox-stub" :data-checked="String(modelValue)" :data-disabled="String(Boolean(disabled))" @click="$emit(\'update:modelValue\', !modelValue)"><slot /></label>',
}
const iconStub = { template: '<span><slot /></span>' }
const uploadStub = {
  props: { disabled: Boolean, drag: Boolean, accept: String, name: String, showFileList: Boolean },
  template:
    '<div class="upload-stub" :data-disabled="String(Boolean(disabled))" :data-drag="String(Boolean(drag))" :data-accept="accept" :data-name="name" :data-show-file-list="String(Boolean(showFileList))"><slot /></div>',
}

describe('import upload dialog', () => {
  it('renders shared import controls and emits the option value', async () => {
    const httpRequest = vi.fn()
    const wrapper = mount(ImportUploadDialog, {
      props: {
        modelValue: true,
        title: '导入学生',
        contextLabel: '目标班级',
        contextValue: '一班',
        optionValue: true,
        optionLabel: '更新已有学生',
        optionDisabled: true,
        uploadDisabled: false,
        uploading: false,
        uploadIdleText: '拖拽学生名单文件到这里',
        httpRequest,
      },
      global: {
        stubs: {
          'el-button': buttonStub,
          'el-checkbox': checkboxStub,
          'el-dialog': dialogStub,
          'el-icon': iconStub,
          'el-upload': uploadStub,
        },
      },
    })

    expect(wrapper.text()).toContain('导入学生')
    expect(wrapper.text()).toContain('下载模板')
    expect(wrapper.text()).toContain('更新已有学生')
    expect(wrapper.text()).toContain('目标班级')
    expect(wrapper.text()).toContain('一班')
    expect(wrapper.text()).toContain('拖拽学生名单文件到这里')
    expect(wrapper.text()).toContain('或点击选择 .xlsx / .xlsm 文件')
    expect(wrapper.find('.upload-stub').attributes('data-drag')).toBe('true')
    expect(wrapper.find('.upload-stub').attributes('data-accept')).toBe('.xlsx,.xlsm')
    expect(wrapper.find('.upload-stub').attributes('data-show-file-list')).toBe('false')

    await wrapper.find('.checkbox-stub').trigger('click')

    expect(wrapper.emitted('update:optionValue')?.[0]).toEqual([false])
  })
})
