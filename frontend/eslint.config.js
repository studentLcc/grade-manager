import pluginVue from 'eslint-plugin-vue'
import vueTsEslintConfig from '@vue/eslint-config-typescript'

export default [
  {
    ignores: ['dist/**', 'node_modules/**', '**/*.tsbuildinfo'],
  },
  ...pluginVue.configs['flat/recommended'],
  ...vueTsEslintConfig(),
  {
    files: ['**/*.{ts,vue}'],
    rules: {
      'vue/max-attributes-per-line': 'off',
      'vue/multi-word-component-names': 'off',
      'vue/singleline-html-element-content-newline': 'off',
    },
  },
]
