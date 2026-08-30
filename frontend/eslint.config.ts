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

      // Una costante usata prima della propria dichiarazione non e' un errore
      // di sintassi: il codice compila, i tipi passano, e la pagina muore
      // all'apertura con «Cannot access ... before initialization». In
      // `<script setup>` capita facilmente, perche' un `watch` con `immediate`
      // o un `onMounted` eseguono subito funzioni scritte in cima che leggono
      // variabili dichiarate piu' sotto. E' successo quattro volte prima di
      // accendere questa regola.
      //
      // Le funzioni restano escluse: sono sollevate, e vietarle costringerebbe
      // a scrivere ogni file dal basso verso l'alto.
      '@typescript-eslint/no-use-before-define': [
        'error',
        { functions: false, classes: true, variables: true },
      ],
    },
  },
)
