<template>
  <v-timeline-item fill-dot color="primary">
    <v-card>
      <v-card-subtitle
        >{{ item.time }}
        <v-icon color="success">{{ mdiCheck }}</v-icon></v-card-subtitle
      >
      <v-card-text class="hash">{{ item.hash }}</v-card-text>
    </v-card>
    <template #icon>
      <v-avatar
          color="primary"
        ><span class="white--text icon">{{ item.icon }}</span></v-avatar
      ></template
    >
  </v-timeline-item>
</template>

<script setup lang="ts">
import { mdiCheck } from '@mdi/js'
import { TickItemDisplay } from '~/utils/uits'

const props = defineProps<{
    item: TickItemDisplay
}>()
</script>

<style scoped>
.hash {
  font-family: Roboto Mono, monospace;
  word-break: break-all;
}

.icon {
  font-family: Roboto Mono, monospace;
  line-height: 0.9;
  white-space: pre-line;
}
</style>
