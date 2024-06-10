<template>
  <v-container>
    <v-card>
      <v-card-title><h1>Hello, vuetify</h1></v-card-title>
      <v-card-text><p>Hello everyone</p></v-card-text>
    </v-card>
    <v-row class="mt-2">
      <v-col cols="6"
        ><Timeline :items="ts.tickItems" :progress-to-next="progressToNext"
      /></v-col>
    </v-row>
  </v-container>
</template>
<script setup lang="ts">
import { useHead } from "unhead"

useHead({
  title: "Startseite",
})
const runtimeConfig = useRuntimeConfig()
const ts = useTimestampService(runtimeConfig.public.authority)
const now = useNow()

const progressToNext = computed(() => {
  if (!ts.value.estimatedNextTick || !ts.value.averageTickDurationMillis) {
    return
  }
  let diff =
    (ts.value.estimatedNextTick.getTime() - now.value.getTime()) /
    ts.value.averageTickDurationMillis
  if (diff < 0) {
    diff = 0
  }
  if (diff > 1.0) {
    diff = 1.0
  }
  diff = (1.0 - diff) * 100
  diff = (100.0 / 80.0) * diff - (20 * 100) / 80
  if (diff < 0) {
    diff = 0
  }
  return diff
})
</script>
