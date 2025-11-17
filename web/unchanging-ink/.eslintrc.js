module.exports = {
  root: true,
  env: {
    browser: true,
    node: true,
  },
  parserOptions: {
    ecmaVersion: 2022,
    sourceType: 'module',
  },
  extends: [
    'eslint:recommended',
    'plugin:vue/vue3-recommended',
    'plugin:prettier/recommended',
  ],
  plugins: [],
  // add your custom rules here
  rules: {
    'vue/multi-word-component-names': 'off',
  },
  globals: {
    defineNuxtConfig: 'readonly',
    defineI18nConfig: 'readonly',
    defineNuxtPlugin: 'readonly',
    useAsyncData: 'readonly',
    useRoute: 'readonly',
    queryContent: 'readonly',
  },
}
