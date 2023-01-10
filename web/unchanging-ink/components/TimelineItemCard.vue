<template>
  <v-timeline-item fill-dot color="primary" right>
    <v-card>
      <v-card-subtitle
        >{{ item.time }}
        <v-icon color="success">{{ mdiCheck }}</v-icon></v-card-subtitle
      >
      <v-card-text class="hash">{{ item.hash }}</v-card-text>
    </v-card>
    <template #icon>
      <v-avatar
        ><span class="white--text icon">{{ item.icon }}</span></v-avatar
      ></template
    >
  </v-timeline-item>
</template>

<script>
import { mdiCheck } from '@mdi/js'

export default {
  name: 'TimelineItemCard',
  props: {
    item: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {
      mdiCheck,
    }
  },
}
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
