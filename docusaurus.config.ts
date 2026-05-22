import {themes as prismThemes} from 'prism-react-renderer';
import type {Config} from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';

const config: Config = {
  title: 'Software Security Foundation',
  tagline: 'Tài liệu nền tảng về An toàn Phần mềm: Formal Methods, BMC, SMT và Fuzzing',
  favicon: 'img/favicon.ico',

  future: {
    v4: true,
    faster: true,
  },

  url: 'https://tuandung222.github.io',
  baseUrl: '/Temp1/',

  organizationName: 'tuandung222',
  projectName: 'Temp1',
  trailingSlash: false,

  onBrokenLinks: 'warn',

  i18n: {
    defaultLocale: 'vi',
    locales: ['vi'],
    localeConfigs: {
      vi: {label: 'Tiếng Việt', htmlLang: 'vi-VN'},
    },
  },

  markdown: {
    mermaid: true,
    hooks: {
      onBrokenMarkdownLinks: 'warn',
    },
  },

  themes: ['@docusaurus/theme-mermaid'],

  stylesheets: [
    {
      href: 'https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css',
      type: 'text/css',
      integrity:
        'sha384-nB0miv6/jRmo5UMMR1wu3Gz6NLsoTkbqJghGIsx//Rlm+ZU03BU6SQNC66uf4l5+',
      crossorigin: 'anonymous',
    },
  ],

  presets: [
    [
      'classic',
      {
        docs: {
          sidebarPath: './sidebars.ts',
          routeBasePath: 'docs',
          editUrl:
            'https://github.com/tuandung222/Temp1/edit/main/',
          remarkPlugins: [remarkMath],
          rehypePlugins: [rehypeKatex],
          showLastUpdateTime: true,
          numberPrefixParser: false,
        },
        blog: false,
        theme: {
          customCss: './src/css/custom.css',
        },
      } satisfies Preset.Options,
    ],
  ],

  plugins: [
    [
      require.resolve('@easyops-cn/docusaurus-search-local'),
      {
        hashed: true,
        language: ['en', 'vi'],
        indexBlog: false,
        docsRouteBasePath: '/docs',
        highlightSearchTermsOnTargetPage: true,
        explicitSearchResultPath: true,
      },
    ],
  ],

  themeConfig: {
    image: 'img/social-card.png',
    colorMode: {
      defaultMode: 'dark',
      respectPrefersColorScheme: true,
    },
    mermaid: {
      theme: {light: 'neutral', dark: 'dark'},
    },
    navbar: {
      title: 'Software Security Foundation',
      logo: {
        alt: 'SSF Logo',
        src: 'img/logo.svg',
      },
      items: [
        {
          type: 'docSidebar',
          sidebarId: 'lectureSidebar',
          position: 'left',
          label: 'Bài giảng',
        },
        {
          to: '/docs/exercises/',
          label: 'Bài tập',
          position: 'left',
        },
        {
          href: 'https://github.com/tuandung222/Temp1',
          label: 'GitHub',
          position: 'right',
        },
      ],
    },
    footer: {
      style: 'dark',
      links: [
        {
          title: 'Bài giảng',
          items: [
            {label: 'Giới thiệu', to: '/docs/intro'},
            {label: 'Lecture 1-2', to: '/docs/01-introduction/01-overview'},
            {label: 'Lecture 3', to: '/docs/02-static-analysis-i/01-overview'},
            {label: 'Lecture 4', to: '/docs/03-static-analysis-ii/01-overview'},
            {label: 'Lecture 5', to: '/docs/04-dynamic-analysis/01-overview'},
            {label: 'Case Study', to: '/docs/05-case-study/01-overview'},
            {label: 'Topics Bổ sung', to: '/docs/06-additional-topics/01-overview'},
            {label: 'Phân tích Code', to: '/docs/07-code-analysis/01-overview'},
          ],
        },
        {
          title: 'Tài nguyên',
          items: [
            {label: 'PDF gốc', to: '/docs/resources/pdfs'},
            {label: 'Bài tập', to: '/docs/exercises/'},
            {label: 'Thuật ngữ', to: '/docs/resources/glossary'},
          ],
        },
        {
          title: 'Liên kết',
          items: [
            {
              label: 'GitHub repo',
              href: 'https://github.com/tuandung222/Temp1',
            },
            {
              label: 'License (CC BY 4.0)',
              href: 'https://creativecommons.org/licenses/by/4.0/',
            },
          ],
        },
      ],
      copyright: `Bản quyền © ${new Date().getFullYear()} Software Security Foundation. Nội dung phát hành theo CC BY 4.0. Trang web xây dựng bằng Docusaurus.`,
    },
    prism: {
      theme: prismThemes.oneLight,
      darkTheme: prismThemes.oneDark,
      additionalLanguages: ['c', 'cpp', 'bash', 'sql', 'python', 'java', 'json'],
    },
  } satisfies Preset.ThemeConfig,
};

export default config;
