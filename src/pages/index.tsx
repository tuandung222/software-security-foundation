import type {ReactNode} from 'react';
import Link from '@docusaurus/Link';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import Layout from '@theme/Layout';
import Heading from '@theme/Heading';

import styles from './index.module.css';

function HomepageHeader(): ReactNode {
  const {siteConfig} = useDocusaurusContext();
  return (
    <header className={styles.hero}>
      <div className={styles.heroInner}>
        <Heading as="h1" className={styles.heroTitle}>
          {siteConfig.title}
        </Heading>
        <p className={styles.heroTagline}>{siteConfig.tagline}</p>
        <div className={styles.heroButtons}>
          <Link
            className={`button button--primary button--lg ${styles.heroButton}`}
            to="/docs/intro">
            Bắt đầu đọc
          </Link>
          <Link
            className={`button button--secondary button--lg ${styles.heroButton}`}
            to="/docs/01-introduction/01-overview">
            Vào Phần 1
          </Link>
        </div>
      </div>
    </header>
  );
}

type LectureCardProps = {
  number: string;
  title: string;
  description: string;
  to: string;
  status?: 'ready' | 'wip';
};

function LectureCard({number, title, description, to, status = 'ready'}: LectureCardProps): ReactNode {
  return (
    <Link to={to} className={styles.card}>
      <div className={styles.cardNumber}>{number}</div>
      <Heading as="h3" className={styles.cardTitle}>
        {title}
      </Heading>
      <p className={styles.cardDescription}>{description}</p>
      <span className={status === 'ready' ? styles.badgeReady : styles.badgeWip}>
        {status === 'ready' ? 'Hoàn thành' : 'Đang biên soạn'}
      </span>
    </Link>
  );
}

function LectureGrid(): ReactNode {
  return (
    <section className={styles.gridSection}>
      <div className="container">
        <Heading as="h2" className={styles.sectionTitle}>
          Bảy phần bài giảng
        </Heading>
        <p className={styles.sectionSubtitle}>
          Lộ trình từ khái niệm cơ bản tới các kỹ thuật verification và fuzzing hiện đại.
        </p>
        <div className={styles.grid}>
          <LectureCard
            number="01"
            title="Software Security là gì?"
            description="CIA Triad, các lớp lỗ hổng phổ biến (buffer overflow, SQL injection, XSS, race condition), và giới thiệu formal verification."
            to="/docs/01-introduction/01-overview"
            status="ready"
          />
          <LectureCard
            number="02"
            title="Static Analysis I (BMC + SMT)"
            description="Đi sâu vào cách dịch chương trình C thành công thức SMT, encoding số nguyên, floating-point và pointer."
            to="/docs/02-static-analysis-i/01-overview"
            status="ready"
          />
          <LectureCard
            number="03"
            title="Static Analysis II (Concurrency)"
            description="Kiểm chứng chương trình đa luồng: context-bounded analysis, lazy exploration, sequentialization."
            to="/docs/03-static-analysis-ii/01-overview"
            status="ready"
          />
          <LectureCard
            number="04"
            title="Dynamic Analysis (Fuzzing)"
            description="Testing, coverage criteria, runtime monitoring với LTL/Büchi, và fuzzing từ AFL đến whitebox symbolic execution."
            to="/docs/04-dynamic-analysis/01-overview"
            status="ready"
          />
          <LectureCard
            number="05"
            title="Case Study (Tư vấn dự án)"
            description="Áp dụng kỹ thuật đã học vào 4 bối cảnh thực tế: Web/SaaS, Fintech, IoT, Doanh nghiệp số hoá."
            to="/docs/05-case-study/01-overview"
            status="ready"
          />
          <LectureCard
            number="06"
            title="Topics Bổ sung"
            description="Cryptography basics, OWASP Top 10 chi tiết, CBMC tutorial, Secure SDLC + Microsoft SDL + OWASP SAMM."
            to="/docs/06-additional-topics/01-overview"
            status="ready"
          />
          <LectureCard
            number="07"
            title="Phân tích Code C/C++"
            description="Đọc lại 39 code pattern từ Lec 1-5 và exercise: chỉ ra bug, giải thích cơ chế, fix với CBMC/ASan/MSan/TSan, CWE và CVSS classification."
            to="/docs/07-code-analysis/01-overview"
            status="ready"
          />
        </div>
      </div>
    </section>
  );
}

function PhilosophySection(): ReactNode {
  return (
    <section className={styles.philosophy}>
      <div className="container">
        <blockquote className={styles.quote}>
          <p>
            <em>"Program testing can be used to show the presence of bugs, but never to
            show their absence."</em>
          </p>
          <footer>Edsger Dijkstra, 1972</footer>
        </blockquote>
        <p className={styles.philosophyText}>
          Tài liệu này dành nhiều tâm sức cho hai câu hỏi cốt lõi: làm thế nào để
          <strong> chứng minh </strong> một chương trình không có một lớp lỗi nào đó, và
          khi chưa chứng minh được, làm thế nào để <strong> tìm phản ví dụ </strong> một
          cách có hệ thống. Hai câu hỏi đó dẫn tới hai họ kỹ thuật chính là Bounded
          Model Checking (static) và Fuzzing (dynamic), gặp nhau ở cuối tài liệu khi BMC
          được dùng để sinh test case.
        </p>
      </div>
    </section>
  );
}

export default function Home(): ReactNode {
  const {siteConfig} = useDocusaurusContext();
  return (
    <Layout
      title={siteConfig.title}
      description={siteConfig.tagline as string}>
      <HomepageHeader />
      <main>
        <LectureGrid />
        <PhilosophySection />
      </main>
    </Layout>
  );
}
