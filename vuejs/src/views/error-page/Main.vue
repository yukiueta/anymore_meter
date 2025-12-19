<template>
  <div class="error-page flex flex-col lg:flex-row items-center justify-center h-screen text-center lg:text-left">
    <div class="-intro-x lg:mr-20">
      <div class="text-8xl font-medium">404</div>
      <div class="text-xl lg:text-3xl font-medium mt-5">ページが見つかりません</div>
      <div class="text-lg mt-3">お探しのページは存在しないか、移動した可能性があります。</div>
    </div>
    <div class="intro-x mt-10 lg:mt-0">
      <router-link to="/" class="btn btn-primary py-3 px-4">ホームに戻る</router-link>
    </div>
  </div>
</template>

<script>
export default {}
</script>