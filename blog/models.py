from django.db import models
from django.urls import reverse
from django.db.models import Count, Prefetch
from django.contrib.auth.models import User


class PostQuerySet(models.QuerySet):

    def annotate_likes(self):
        return self.annotate(likes_count=Count('likes'))

    def popular_posts(self):
        return self.annotate_likes().order_by('-likes_count')

    def fresh_posts(self):
        return self.annotate(comments_count=Count('comments'))\
            .order_by('-published_at')

    def fetch_with_comments_count(self):
        posts_ids = [post.id for post in self]
        posts_with_comments = Post.objects.filter(id__in=posts_ids).annotate(comments_count=Count('comments'))
        ids_and_comments = dict(posts_with_comments.values_list('id', 'comments_count'))

        for post in self:
            post.comments_count = ids_and_comments[post.id]
        return list(self)

    def annotate_tags(self):
        prefetch = Prefetch(
            'tags', queryset=Tag.objects.posts_count()
        )
        return self.prefetch_related(prefetch)


class Post(models.Model):
    title = models.CharField("Заголовок", max_length=200)
    text = models.TextField("Текст")
    slug = models.SlugField("Название в виде url", max_length=200)
    image = models.ImageField("Картинка")
    published_at = models.DateTimeField("Дата и время публикации")

    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Автор", limit_choices_to={'is_staff': True})
    likes = models.ManyToManyField(User, related_name="liked_posts", verbose_name="Кто лайкнул", blank=True)
    tags = models.ManyToManyField("Tag", related_name="posts", verbose_name="Теги")

    objects = PostQuerySet.as_manager()

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('post_detail', args={'slug': self.slug})

    class Meta:
        ordering = ['-published_at']
        verbose_name = 'пост'
        verbose_name_plural = 'посты'


class TagQuerySet(models.QuerySet):

    def popular_tags(self):
        return self.annotate(posts_count=Count('posts'))\
            .order_by('-posts_count')

    def posts_count(self):
        return self.annotate(posts_count=Count('posts'))


class Tag(models.Model):
    title = models.CharField("Тег", max_length=20, unique=True)

    objects = TagQuerySet.as_manager()

    def __str__(self):
        return self.title

    def clean(self):
        self.title = self.title.lower()

    def get_absolute_url(self):
        return reverse('tag_filter', args={'tag_title': self.slug})

    class Meta:
        ordering = ["title"]
        verbose_name = 'тег'
        verbose_name_plural = 'теги'


class Comment(models.Model):
    post = models.ForeignKey("Post", on_delete=models.CASCADE,
                             verbose_name="Пост, к которому написан", related_name="comments")
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Автор")

    text = models.TextField("Текст комментария")
    published_at = models.DateTimeField("Дата и время публикации")

    def __str__(self):
        return f"{self.author.username} under {self.post.title}"

    class Meta:
        ordering = ['published_at']
        verbose_name = 'комментарий'
        verbose_name_plural = 'комментарии'
