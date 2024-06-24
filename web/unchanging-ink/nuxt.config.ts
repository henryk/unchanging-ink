// https://nuxt.com/docs/api/configuration/nuxt-config
import vuetify, { transformAssetUrls } from "vite-plugin-vuetify"
import type { ViteConfig } from "@nuxt/schema"

export default defineNuxtConfig({
  runtimeConfig: {
    public: {
      authority: "http://localhost:23230",
    },
  },
  css: ["@fontsource/roboto", "vuetify/styles/main.sass"],
  vite: {
    vue: {
      template: {
        transformAssetUrls,
      },
    },
    server: {
      watch: {
        usePolling: true,
        interval: 300,
      },
    },
  },
  app: {
    head: {
      htmlAttrs: {
        lang: "de",
      },
      meta: [
        { charset: "utf-8" },
        { name: "viewport", content: "width=device-width, initial-scale=1" },
      ],
      link: [{ rel: "icon", type: "image/x-icon", href: "/favicon.ico" }],
      title: "unchanging.ink",
      titleTemplate: "%s - unchanging.ink",
    },
  },
  build: {
    transpile: ["vuetify"],
  },
  modules: [
    "@nuxtjs/i18n",
    "@vueuse/nuxt",
    (_options, nuxt) => {
      nuxt.hooks.hook("vite:extendConfig", (config) => {
        // @ts-expect-error
        config.plugins.push(vuetify({ autoImport: true }))
      })
    },
  ],
  hooks: {
    "vite:extendConfig": (config: ViteConfig) => {
      config.plugins = [...(config.plugins ?? []), vuetify({})]
    },
  },
  i18n: {
    locales: ["en", "de"],
    defaultLocale: "de",
  },
})
