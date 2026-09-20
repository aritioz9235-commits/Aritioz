'use client';

import { useState } from 'react';
import {
  ArrowUpRight,
  BadgeIndianRupee,
  Bot,
  Box,
  ChartNoAxesCombined,
  CircleDollarSign,
  ClipboardList,
  Globe2,
  Image,
  LayoutDashboard,
  MessageCircle,
  Package,
  Palette,
  Send,
  ShoppingBag,
  Sparkles,
  Store,
  WandSparkles,
} from 'lucide-react';

const modules = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard, eyebrow: 'LaunchOS overview', title: 'Good evening, Ansh.', description: 'Your brand is taking shape. Complete the next step to publish your store.' },
  { id: 'brand', label: 'AI Brand Studio', icon: Palette, eyebrow: 'Create your identity', title: 'Build a brand people remember.', description: 'Generate a name, logo, tagline, colours, fonts and story from one product photo.' },
  { id: 'products', label: 'Product Studio', icon: Package, eyebrow: 'Product intelligence', title: 'Turn a product into a listing.', description: 'Improve images, write titles and descriptions, and assign the right category.' },
  { id: 'packaging', label: 'Packaging Studio', icon: Box, eyebrow: 'Packaging concepts', title: 'Make every unboxing feel premium.', description: 'Create box, bottle, label and pouch mockups in your brand language.' },
  { id: 'pricing', label: 'Pricing Assistant', icon: CircleDollarSign, eyebrow: 'Smart pricing', title: 'Price for profitable growth.', description: 'Calculate cost, margins, discounts and a clear selling-price recommendation.' },
  { id: 'store', label: 'Store Builder', icon: Store, eyebrow: 'Your storefront', title: 'Launch a store in minutes.', description: 'Choose a template, add your catalogue, and set up cart, checkout and your domain.' },
  { id: 'content', label: 'AI Content Studio', icon: Image, eyebrow: 'Content engine', title: 'Create content that keeps selling.', description: 'Plan Instagram posts, captions, ads and Reels scripts for every product launch.' },
  { id: 'whatsapp', label: 'WhatsApp Selling', icon: Send, eyebrow: 'Direct selling', title: 'Close the conversation faster.', description: 'Share your catalogue, reply to enquiries and send order notifications on WhatsApp.' },
  { id: 'agent', label: 'AI Sales Agent', icon: Bot, eyebrow: 'Phase 3 / Growth', title: 'Let your store answer while you build.', description: 'Handle product questions, collect leads, follow up and recover abandoned carts.' },
  { id: 'orders', label: 'Order Management', icon: ShoppingBag, eyebrow: 'Fulfilment', title: 'Every order, under control.', description: 'Track new, confirmed, shipped, delivered and returned orders in one place.' },
  { id: 'analytics', label: 'Analytics', icon: ChartNoAxesCombined, eyebrow: 'Business intelligence', title: 'Know what drives your growth.', description: 'See sales, visitors, popular products, conversion and profit at a glance.' },
  { id: 'plans', label: 'Plans & billing', icon: BadgeIndianRupee, eyebrow: 'LaunchOS plans', title: 'Choose the pace that fits your business.', description: 'Start free, then unlock more product capacity and growth tools as you scale.' },
];

const moduleFeatures: Record<string, string[]> = {
  brand: ['AI brand name, logo and tagline', 'Colour palette and font pairing', 'Brand story and downloadable kit'],
  products: ['Background removal and image enhancement', 'Bilingual title and product description', 'Suggested category and product details'],
  packaging: ['Box, bottle, label and pouch concepts', 'Ready-to-review visual mockups', 'Consistent brand colours and typography'],
  pricing: ['Cost and profit-margin calculator', 'Discount planning', 'Suggested selling price'],
  store: ['Store template and custom domain', 'Catalogue, cart and checkout', 'Shareable seller store link'],
  content: ['Instagram posts and captions', 'Ad copy and Reels scripts', 'Campaign-ready content calendar'],
  whatsapp: ['Shareable WhatsApp catalogue', 'Enquiry replies and quick responses', 'Order notification templates'],
  agent: ['Product question replies', 'Lead collection and follow-ups', 'Cart-recovery prompts'],
  orders: ['New to delivered order status', 'Payment and customer details', 'Returns overview'],
  analytics: ['Sales and visitor trends', 'Popular products and conversion', 'Profit insights'],
};

const plans = [
  ['Free', '₹0', '3 products · basic store'],
  ['Launch Pack', '₹499', 'Brand kit · store launch'],
  ['Seller Pro', '₹999/mo', '50 products · AI content · WhatsApp'],
  ['Business', '₹2,999/mo', '500 products · analytics · Sales Agent'],
  ['Agency', '₹7,999/mo', 'Multiple brands · white-label'],
];

export function LaunchOSWorkspace() {
  const [activeId, setActiveId] = useState('dashboard');
  const active = modules.find((module) => module.id === activeId) ?? modules[0];
  const Icon = active.icon;

  return (
    <div className="dashboard-preview launchos-workspace" aria-label="Aritioz LaunchOS seller workspace">
      <div className="dashboard-topbar">
        <span className="dashboard-brand"><Sparkles size={15} /> aritioz <em>LaunchOS</em></span>
        <span className="dashboard-avatar">AK</span>
      </div>
      <div className="dashboard-body">
        <aside className="dashboard-sidebar">
          <span className="sidebar-label">Seller workspace</span>
          <nav aria-label="LaunchOS modules">
            {modules.map((module) => {
              const NavIcon = module.icon;
              return <button key={module.id} className={activeId === module.id ? 'active' : ''} onClick={() => setActiveId(module.id)}><NavIcon size={15} />{module.label}</button>;
            })}
          </nav>
        </aside>
        <div className="dashboard-main">
          {activeId === 'dashboard' ? <DashboardHome onNavigate={setActiveId} /> : activeId === 'plans' ? <Plans /> : <ModuleView active={active} Icon={Icon} />}
        </div>
      </div>
    </div>
  );
}

function DashboardHome({ onNavigate }: { onNavigate: (id: string) => void }) {
  return <>
    <div className="dashboard-welcome">
      <div><p>Sunday, 7 September</p><h3>Good evening, Ansh.</h3></div>
      <button onClick={() => onNavigate('products')}>+ Add product</button>
    </div>
    <div className="quick-start-card">
      <div><span>LaunchOS / MVP</span><h4>Your store is 72% ready</h4><p>Upload one product, build your brand, then publish your mini-store.</p></div>
      <Sparkles size={28} />
    </div>
    <div className="metric-grid">
      <article><span>Today&apos;s sales</span><strong>₹ 12,480</strong><em>+18.4%</em></article>
      <article><span>New orders</span><strong>24</strong><em>+12 today</em></article>
      <article><span>Store visits</span><strong>1,284</strong><em>+26.8%</em></article>
    </div>
    <div className="dashboard-lower">
      <article className="product-card"><span>Featured product</span><div className="product-image"><Package size={26} /></div><strong>Organic Face Serum</strong><p>₹ 899 · 18 in stock</p></article>
      <article className="agent-card"><div><MessageCircle size={18} /><span>Next launch step</span></div><strong>Use AI Brand Studio to create your first brand kit.</strong><button onClick={() => onNavigate('brand')}>Create brand <ArrowUpRight size={14} /></button></article>
    </div>
    <div className="launch-roadmap"><span>Launch roadmap</span><strong>Phase 1: LaunchOS</strong><p>Product upload → brand → mini-store → payments → orders.</p></div>
  </>;
}

function ModuleView({ active, Icon }: { active: typeof modules[number]; Icon: typeof Sparkles }) {
  const features = moduleFeatures[active.id] ?? [];
  return <div className="module-view">
    <div className="module-hero"><div><p>{active.eyebrow}</p><h3>{active.title}</h3><span>{active.description}</span></div><Icon size={32} /></div>
    <div className="module-feature-list">
      {features.map((feature, index) => <article key={feature}><span>0{index + 1}</span><strong>{feature}</strong><WandSparkles size={17} /></article>)}
    </div>
    <div className="module-note"><ClipboardList size={17} /><span>MVP focus: make this task simple, fast and ready to publish.</span></div>
  </div>;
}

function Plans() {
  return <div className="plans-view">
    <div className="module-hero"><div><p>LaunchOS pricing</p><h3>Start free. Scale when ready.</h3><span>Transaction fee: 1–2% on successful orders.</span></div><BadgeIndianRupee size={32} /></div>
    <div className="plan-grid">{plans.map(([name, price, copy]) => <article key={name}><span>{name}</span><strong>{price}</strong><p>{copy}</p></article>)}</div>
  </div>;
}
