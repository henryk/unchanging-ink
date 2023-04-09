<template>
  <v-app>
    <v-navigation-drawer v-model="drawer" :clipped="clipped" fixed app>
      <v-list>
        <v-list-item
          v-for="item in items"
          :key="item.icon"
          :to="item.to"
          router
          exact
        >
          <v-list-item-action>
            <v-icon>{{ item.icon }}</v-icon>
          </v-list-item-action>
          <v-list-item-title v-text="item.title" />
        </v-list-item>
      </v-list>
    </v-navigation-drawer>
    <v-app-bar :clipped-left="clipped" fixed app>
      <v-app-bar-nav-icon @click.stop="drawer = !drawer" />
      <v-toolbar-title v-text="title" />
      <v-spacer />
    </v-app-bar>
    <v-main>
      <v-container>
        <NuxtLayout>
          <NuxtPage/>
        </NuxtLayout>
      </v-container>
    </v-main>
    <v-footer :absolute="!fixed" app>
      <span>&copy; 2023</span>
      <v-spacer></v-spacer>
      <v-icon class="px-2">{{ mdiTranslate }}</v-icon>
      <NuxtLink
        v-for="locale in availableLocales"
        :key="locale.code"
        :to="switchLocalePath(locale.code)"
        >{{ locale.name }}</NuxtLink
      >
    </v-footer>
  </v-app>
</template>

<script setup>
import { mdiHome, mdiBookOpenVariant, mdiTranslate } from '@mdi/js'
const switchLocalePath = useSwitchLocalePath()

const { t, locale, locales } = useI18n()

const availableLocales = computed(() => {
  return (locales.value).filter(i => i.code !== locale.value)
})

let clipped = ref(false)
let drawer = ref(false)
let fixed = ref(false)
const items = [
        {
          icon: mdiHome,
          title: t('homepage'),
          to: '/',
        },
        {
          icon: mdiBookOpenVariant,
          title: 'Documentation',
          to: '/doc/',
        },
      ]
let right = ref(true)

useHead({
  title: 'unchanging.ink -- ' + t('timestampService')
})

</script>
<i18n lang="yaml">
de:
  timestampService: Zeitstempeldienst
  homepage: Startseite
en:
  timestampService: Timestamp Service
  homepage: Home Page
</i18n>
