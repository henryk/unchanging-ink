<template>
  <article>
    <ContentDoc :path="`/doc/${route.params.slug}`" />
  </article>
</template>

<script setup>
const route = useRoute()
</script>
