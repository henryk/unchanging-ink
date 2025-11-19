<template>
  <div>
    <div v-if="!article">Loading or no article found...</div>
    <article v-else>
      <ContentRenderer :value="article" />
    </article>
  </div>
</template>

<script setup lang="ts">
const route = useRoute()
const slug = String(route.params.slug)

const { data: article, error } = await useAsyncData(`doc-${slug}`, () =>
  queryContent(`/doc/${slug}`).findOne(),
)

if (process.client) {
  console.log(`Doc ${slug} article:`, article.value)
  console.log(`Doc ${slug} error:`, error.value)
}
</script>
