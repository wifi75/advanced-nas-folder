import js from '@eslint/js'
import globals from 'globals'
import pluginVue from 'eslint-plugin-vue'
import tseslint from 'typescript-eslint'

export default tseslint.config(
  { ignores: ['dist/**', 'node_modules/**'] },
  js.configs.recommended,
  ...tseslint.configs.recommended,
  ...pluginVue.configs['flat/recommended'],
  {
    // Il pannello gira nel browser: senza dichiararne i global, regole come
    // `no-undef` segnalano `document`, `File` o `DragEvent` come nomi
    // inesistenti, e si finisce per scriverli come `globalThis.qualcosa` solo
    // per far tacere il linter.
    files: ['src/**/*.{ts,vue}'],
    languageOptions: {
      globals: globals.browser,
      parserOptions: { parser: tseslint.parser },
    },
  },
  {
    rules: {
      'vue/multi-word-component-names': 'off',
    },
  },
)
