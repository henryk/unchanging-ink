<template>
  <div>
    <div v-if="!article">Loading or no article found...</div>
    <article v-else>
      <ContentRenderer :value="article" />
    </article>
  </div>
</template>

<script setup lang="ts">
const { data: article, error } = await useAsyncData('doc-index', () =>
  queryContent('/doc/index').findOne(),
)

if (process.client) {
  console.log('Doc index article:', article.value)
  console.log('Doc index error:', error.value)
}
</script>
