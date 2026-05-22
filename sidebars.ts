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
        '02-static-analysis-i/02-verification-vs-validation',
        '02-static-analysis-i/03-state-space-exploration',
        '02-static-analysis-i/04-sat-and-dpll',
        '02-static-analysis-i/05-smt-theories',
        '02-static-analysis-i/06-encoding-numbers-and-floats',
        '02-static-analysis-i/07-encoding-pointers-and-memory',
      ],
    },
    {
      type: 'category',
      label: 'Lecture 4: Static Analysis II (Concurrency)',
      link: {type: 'doc', id: '03-static-analysis-ii/01-overview'},
      collapsed: false,
      items: [
        '03-static-analysis-ii/01-overview',
        '03-static-analysis-ii/02-loop-unwinding-and-safety',
        '03-static-analysis-ii/03-bit-blasting-and-arrays',
        '03-static-analysis-ii/04-concurrency-verification',
        '03-static-analysis-ii/05-context-bounded-analysis',
        '03-static-analysis-ii/06-lazy-vs-schedule-recording',
        '03-static-analysis-ii/07-sequentialization-kiss-lr',
      ],
    },
    {
      type: 'category',
      label: 'Lecture 5: Dynamic Analysis (Testing + Fuzzing)',
      link: {type: 'doc', id: '04-dynamic-analysis/01-overview'},
      collapsed: false,
      items: [
        '04-dynamic-analysis/01-overview',
        '04-dynamic-analysis/02-security-testing',
        '04-dynamic-analysis/03-coverage-criteria',
        '04-dynamic-analysis/04-monitoring-ltl-buchi',
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
