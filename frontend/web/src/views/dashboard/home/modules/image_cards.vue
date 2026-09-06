<template>
  <ElCarousel height="400px">
    <ElCarouselItem v-for="card in imageCards" :key="card.id" class="mb-5">
      <FaImageCard
        :imageUrl="card.imageUrl"
        :title="card.title"
        :category="card.category"
        :readTime="card.readTime"
        :views="card.views"
        :comments="card.comments"
        :date="card.date"
        @click="handleImageCardClick(card)"
      />
    </ElCarouselItem>
  </ElCarousel>
</template>

<script setup lang="ts">
import FaImageCard from "@/components/cards/fa-image-card/index.vue";
import cover1 from "@imgs/cover/img1.webp";
import cover2 from "@imgs/cover/img2.webp";
import cover3 from "@imgs/cover/img3.webp";
import cover4 from "@imgs/cover/img4.webp";

defineOptions({ name: "ImageCards" });

// === 卡片演示数据 ← workplace ===
const imageCards = [
  {
    id: 1,
    imageUrl: cover1,
    title: "AI技术在医疗领域的创新应用与发展前景",
    category: "社交",
    readTime: "2分钟",
    views: 9125,
    comments: 3,
    date: "12月19日 周一",
  },
  {
    id: 2,
    imageUrl: cover2,
    title: "大数据分析助力企业决策的实践案例",
    category: "技术",
    readTime: "3分钟",
    views: 7234,
    comments: 5,
    date: "12月20日 周二",
  },
  {
    id: 3,
    imageUrl: cover3,
    title: "区块链技术在供应链管理中的应用",
    category: "科技",
    readTime: "4分钟",
    views: 5678,
    comments: 8,
    date: "12月21日 周三",
  },
  {
    id: 4,
    imageUrl: cover4,
    title: "云计算技术发展趋势与未来展望",
    category: "云技术",
    readTime: "5分钟",
    views: 4321,
    comments: 6,
    date: "12月22日 周四",
  },
];

/**
 * 图片卡片类型定义
 */
interface ImageCard {
  id: number;
  imageUrl: string;
  title: string;
  category: string;
  readTime: string;
  views: number;
  comments: number;
  date: string;
}

/**
 * 处理图片卡片点击事件
 * @param card 卡片数据
 */
const handleImageCardClick = (card: ImageCard) => {
  // TODO: 接入真实跳转
  console.log("点击卡片:", card);
};
</script>
