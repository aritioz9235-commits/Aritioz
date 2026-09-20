import {
  ArrowDown,
  ArrowRight,
  ArrowUpRight,
  BrainCircuit,
  Code2,
  Cpu,
  Layers3,
  PenTool,
  Play,
  Sparkles,
  Workflow,
} from 'lucide-react';
import { Dialog, DialogClose, DialogContent, DialogDescription, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { LaunchOSWorkspace } from '@/components/launchos-workspace';

export default function Home() {
  return (
    <Dialog>
    <main>
      <section className="hero" id="home">
        <div className="hero-backdrop" aria-hidden="true" />
        <div className="hero-grid" aria-hidden="true" />

        <header className="site-header shell">
          <a className="brand" href="#home" aria-label="Aritioz home">
            <span className="brand-mark">
              <Sparkles size={18} strokeWidth={1.7} />
            </span>
            <span>Aritioz</span>
          </a>

          <nav className="nav-links" aria-label="Primary navigation">
            <a href="#home">Home</a>
            <a href="#about">Vision</a>
            <a href="#capabilities">Capabilities</a>
          </nav>

          <DialogTrigger className="header-cta">
            Start a project <ArrowUpRight size={15} />
          </DialogTrigger>
        </header>

        <div className="hero-side hero-side-left" aria-hidden="true">
          <span>01 / Creative intelligence</span>
          <i />
        </div>
        <div className="hero-side hero-side-right" aria-hidden="true">
          <span>Ideas engineered forward</span>
          <i />
        </div>

        <div className="hero-content shell">
          <p className="eyebrow">Designing what comes next</p>
          <h1>
            Where ideas become
            <span>intelligent.</span>
          </h1>
          <p className="hero-copy">
            Aritioz blends strategy, design, and AI to turn ambitious ideas into
            digital experiences built to evolve.
          </p>
          <div className="hero-actions">
            <DialogTrigger className="button button-primary">
              Build with Aritioz <ArrowUpRight size={17} />
            </DialogTrigger>
            <a className="button button-ghost" href="#capabilities">
              <span className="play-icon"><Play size={14} fill="currentColor" /></span>
              Explore our work
            </a>
          </div>
        </div>

        <div className="capability-rail shell" aria-label="Core capabilities">
          <div>
            <BrainCircuit size={23} />
            <p><strong>AI Experiences</strong><span>Useful by design</span></p>
          </div>
          <div>
            <Workflow size={23} />
            <p><strong>Smart Systems</strong><span>Built to adapt</span></p>
          </div>
          <div>
            <Layers3 size={23} />
            <p><strong>Digital Products</strong><span>Ready to scale</span></p>
          </div>
        </div>

        <a className="scroll-cue" href="#about" aria-label="Scroll to vision">
          <ArrowDown size={16} />
        </a>
      </section>

      <section className="definition section-pad" id="about">
        <div className="definition-backdrop" aria-hidden="true" />
        <div className="definition-overlay" aria-hidden="true" />
        <div className="definition-glow" aria-hidden="true" />
        <div className="shell">
          <div className="definition-frame">
            <div className="definition-intro">
              <p className="section-kicker">The idea behind Aritioz</p>
              <p className="definition-index">02 / 04</p>
            </div>
            <div className="definition-title">
              <h2>Aritioz</h2>
              <p><span>/ ar·i·ti·oz /</span> noun · creative intelligence</p>
            </div>
            <p className="definition-copy">
              The point where imagination meets intelligence—and a bold idea
              becomes a clear, useful, beautifully engineered experience.
            </p>
            <div className="definition-note">
              <span>Not just a name.</span>
              <strong>A way of moving ideas forward.</strong>
            </div>
          </div>
        </div>
      </section>

      <section className="process" id="process">
        <div className="process-backdrop" aria-hidden="true" />
        <div className="process-overlay" aria-hidden="true" />
        <div className="shell process-inner">
          <div className="process-heading">
            <p className="section-kicker">From possibility to progress</p>
            <h2>One idea. Three deliberate moves.</h2>
          </div>

          <div className="process-steps">
            <article>
              <span>01 / Discover</span>
              <h3>Find the signal.</h3>
              <p>We uncover the human need, business opportunity, and clearest way forward.</p>
            </article>
            <ArrowRight className="process-arrow" aria-hidden="true" />
            <article>
              <span>02 / Design</span>
              <h3>Shape the system.</h3>
              <p>We turn the strategy into a distinct experience with intelligence built in.</p>
            </article>
            <ArrowRight className="process-arrow" aria-hidden="true" />
            <article>
              <span>03 / Deliver</span>
              <h3>Launch the leap.</h3>
              <p>We build, refine, and release a product designed to learn and grow.</p>
            </article>
          </div>

          <p className="process-manifesto">
            We don&apos;t wait for what&apos;s next.
            <strong>We create it.</strong>
          </p>
        </div>
      </section>

      <section className="capabilities section-pad" id="capabilities">
        <div className="shell">
          <div className="section-heading-row">
            <div>
              <p className="section-kicker">What we make possible</p>
              <h2>Built across disciplines.<br />Focused on one outcome.</h2>
            </div>
            <p>
              Strategy, design, and technology working as one team—so the idea
              stays strong from first thought to final release.
            </p>
          </div>

          <div className="capability-cards">
            <article className="capability-card">
              <div className="card-top"><span>01</span><PenTool size={25} /></div>
              <div>
                <h3>Brand &amp; Product Direction</h3>
                <p>Positioning, experience strategy, product definition, and a visual language people remember.</p>
              </div>
              <ul><li>Strategy</li><li>Identity</li><li>Product vision</li></ul>
            </article>
            <article className="capability-card featured-card">
              <div className="card-top"><span>02</span><Code2 size={25} /></div>
              <div>
                <h3>Digital Experience</h3>
                <p>High-impact websites and products where every interaction feels considered, clear, and alive.</p>
              </div>
              <ul><li>UX / UI</li><li>Web experiences</li><li>Design systems</li></ul>
            </article>
            <article className="capability-card">
              <div className="card-top"><span>03</span><Cpu size={25} /></div>
              <div>
                <h3>Applied Intelligence</h3>
                <p>AI-powered features and workflows made practical, understandable, and genuinely useful.</p>
              </div>
              <ul><li>AI products</li><li>Automation</li><li>Prototyping</li></ul>
            </article>
          </div>
        </div>
      </section>

      <section className="contact-section" id="contact">
        <div className="project-noise" aria-hidden="true" />
        <div className="shell contact-cta">
          <p className="section-kicker">Ready to turn an idea into a business?</p>
          <h2>Your commerce workspace<br />starts here.</h2>
          <DialogTrigger className="button button-primary">
            Start a project <ArrowUpRight size={17} />
          </DialogTrigger>
        </div>
        <DialogContent className="project-dialog" showCloseButton={false}>
          <div className="project-dialog-topbar">
            <div><DialogTitle>Seller Commerce OS</DialogTitle><DialogDescription>Brand, store, sales and customers—in one workspace.</DialogDescription></div>
            <DialogClose className="project-dialog-close" aria-label="Close project workspace">×</DialogClose>
          </div>
          <div className="project-shell">
          <LaunchOSWorkspace />
          </div>
        </DialogContent>
      </section>

      <footer className="footer">
        <div className="shell footer-inner">
          <a className="brand" href="#home" aria-label="Back to top">
            <span className="brand-mark"><Sparkles size={18} strokeWidth={1.7} /></span>
            <span>Aritioz</span>
          </a>
          <p>Creative intelligence for what comes next.</p>
          <span>© 2026 Aritioz</span>
        </div>
      </footer>
    </main>
    </Dialog>
  );
}
