<template>
  <v-app>
    <v-navigation-drawer v-model="drawer" app>
      <v-list>
        <v-list-item v-for="(item, i) in items" :key="i" :to="item.to" link>
          <template #prepend>
            <v-icon :icon="item.icon" />
          </template>
          <v-list-item-title>{{ item.title }}</v-list-item-title>
        </v-list-item>
      </v-list>
    </v-navigation-drawer>
    <v-app-bar app>
      <v-app-bar-nav-icon @click.stop="drawer = !drawer" />
      <v-toolbar-title>{{ title }}</v-toolbar-title>
      <v-spacer />
    </v-app-bar>
    <v-main>
      <v-container>
        <slot />
      </v-container>
    </v-main>
    <v-footer :absolute="!fixed" app>
      <span>&copy; 2025</span>
      <v-spacer></v-spacer>
      <v-icon class="px-2" :icon="mdiTranslate"></v-icon>
      <NuxtLink
        v-for="localeOption in availableLocales"
        :key="localeOption.code"
        :to="switchLocalePath(localeOption.code)"
      >
        {{ localeOption.name }}
      </NuxtLink>
    </v-footer>
  </v-app>
</template>

<script setup>
import { mdiBookOpenVariant, mdiHome, mdiTranslate } from '@mdi/js'
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useSwitchLocalePath } from '#imports'

const { t, locale, locales } = useI18n()
const switchLocalePath = useSwitchLocalePath()

const drawer = ref(false)
const fixed = ref(false)

const items = computed(() => [
  {
    icon: mdiHome,
    title: t('homepage'),
    to: '/',
  }
])

const availableLocales = computed(() =>
  locales.value.filter((i) => i.code !== locale.value)
)
const title = computed(() => `unchanging.ink -- ${t('timestampService')}`)
</script>
<i18n lang="yaml">
de:
  timestampService: Zeitstempeldienst
  homepage: Startseite
en:
  timestampService: Timestamp Service
  homepage: Home Page
</i18n>
.
