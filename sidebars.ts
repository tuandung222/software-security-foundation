import type {SidebarsConfig} from '@docusaurus/plugin-content-docs';

const sidebars: SidebarsConfig = {
  lectureSidebar: [
    'intro',
    {
      type: 'category',
      label: 'Lecture 1-2: Giới thiệu Software Security',
      link: {type: 'doc', id: '01-introduction/01-overview'},
      collapsed: false,
      items: [
        '01-introduction/01-overview',
        '01-introduction/02-cia-and-properties',
        '01-introduction/03-vulnerabilities-catalog',
        '01-introduction/04-web-vulnerabilities',
        '01-introduction/05-formal-verification-intro',
        '01-introduction/06-bmc-and-smt-basics',
      ],
    },
    {
      type: 'category',
      label: 'Lecture 3: Static Analysis I (BMC + SMT)',
      link: {type: 'doc', id: '02-static-analysis-i/01-overview'},
      collapsed: false,
      items: [
        '02-static-analysis-i/01-overview',
      ],
    },
    {
      type: 'category',
      label: 'Lecture 4: Static Analysis II (Concurrency)',
      link: {type: 'doc', id: '03-static-analysis-ii/01-overview'},
      collapsed: false,
      items: [
        '03-static-analysis-ii/01-overview',
      ],
    },
    {
      type: 'category',
      label: 'Lecture 5: Dynamic Analysis (Testing + Fuzzing)',
      link: {type: 'doc', id: '04-dynamic-analysis/01-overview'},
      collapsed: false,
      items: [
        '04-dynamic-analysis/01-overview',
      ],
    },
    {
      type: 'category',
      label: 'Bài tập (Exercises)',
      link: {type: 'doc', id: 'exercises/index'},
      collapsed: true,
      items: [
        'exercises/index',
        'exercises/exercise-set-2',
      ],
    },
    {
      type: 'category',
      label: 'Tài nguyên',
      collapsed: true,
      items: [
        'resources/pdfs',
        'resources/glossary',
        'resources/exam-checklist',
      ],
    },
  ],
};

export default sidebars;
