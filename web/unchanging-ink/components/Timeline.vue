<template>
  <v-card ref="timelineDisplay" :loading="true">
    <template #loader>
      <v-progress-linear
        color="primary"
        :model-value="(paused ? 0 : progressToNext) ?? 0"
        :stream="paused"
      ></v-progress-linear>
    </template>
    <v-card-title class="headline d-flex">
      <span>{{ $t("liveView") }}</span>
      <v-spacer />
      <v-icon v-if="paused">{{ mdiPause }}</v-icon>
      <v-icon v-else>{{ mdiPlay }}</v-icon>
    </v-card-title>
    <v-card-text style="max-height: 35em; overflow-y: hidden">
      <v-timeline v-show="displayItems.length" clipped dense side="end">
        <transition-group name="slide-y-transition">
          <timeline-item-card
            v-for="item in displayItems"
            :key="item.time"
            :item="item"
          ></timeline-item-card>
        </transition-group>
      </v-timeline>
    </v-card-text>
  </v-card>
</template>

<script lang="ts" setup>
import { mdiPause, mdiPlay } from "@mdi/js"
import type { TickItemDisplay } from "~/utils/uits"
import type { Ref } from "vue"

const props = defineProps<{
  progressToNext?: number
  items: Array<TickItemDisplay>
}>()

const timelineDisplay = ref(null)

const pausedItems: Ref<Array<TickItemDisplay>> = ref([])
const { isOutside: mouseIsOutTimeline } = useMouseInElement(timelineDisplay)
const documentIsVisible = useDocumentVisibility()

const displayItems = computed(() => {
  return paused.value ? unref(pausedItems) : unref(props.items)
})
const paused = computed(() => {
  return !mouseIsOutTimeline.value || !documentIsVisible.value
})

watch(
  paused,
  (newVal) => {
    if (newVal) {
      pausedItems.value = [...unref(props.items)]
    }
  },
  { immediate: true },
)
</script>
<i18n lang="yaml">
de:
  liveView: Live-Ansicht
en:
  liveView: Live View
</i18n>
