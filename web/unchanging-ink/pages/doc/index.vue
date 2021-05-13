<template>
  <article>
    <nuxt-content :document="article" />
  </article>
</template>
<script>
export default {
  async asyncData({ $content }) {
    const article = await $content('doc', 'index').fetch()

    return { article }
  },
}
</script>
