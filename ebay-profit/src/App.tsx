import { useEffect, useState } from 'react';
import { StoreProvider, useStore } from './ui/store';
import { Dashboard } from './ui/Dashboard';
import { CandidateDetail } from './ui/CandidateDetail';
import { AddCandidate } from './ui/AddCandidate';
import { Watchlist } from './ui/Watchlist';
import { Settings } from './ui/Settings';

type Route =
  | { name: 'dashboard' }
  | { name: 'detail'; id: string }
  | { name: 'add' }
  | { name: 'watch' }
  | { name: 'settings' };

function parseHash(): Route {
  const h = window.location.hash.replace(/^#\/?/, '');
  if (h.startsWith('detail/')) return { name: 'detail', id: decodeURIComponent(h.slice('detail/'.length)) };
  if (h === 'add') return { name: 'add' };
  if (h === 'watch') return { name: 'watch' };
  if (h === 'settings') return { name: 'settings' };
  return { name: 'dashboard' };
}

function toHash(r: Route): string {
  switch (r.name) {
    case 'detail':
      return `#/detail/${encodeURIComponent(r.id)}`;
    case 'add':
      return '#/add';
    case 'watch':
      return '#/watch';
    case 'settings':
      return '#/settings';
    default:
      return '#/';
  }
}

const TABS: { name: Route['name']; label: string; icon: string }[] = [
  { name: 'dashboard', label: '一覧', icon: '📊' },
  { name: 'add', label: '追加', icon: '＋' },
  { name: 'watch', label: 'ウォッチ', icon: '★' },
  { name: 'settings', label: '設定', icon: '⚙' },
];

function Shell() {
  const { ready, settings, candidates, toastMsg } = useStore();
  const [route, setRoute] = useState<Route>(parseHash);

  useEffect(() => {
    const onHash = () => setRoute(parseHash());
    window.addEventListener('hashchange', onHash);
    return () => window.removeEventListener('hashchange', onHash);
  }, []);

  function go(r: Route) {
    window.location.hash = toHash(r);
    setRoute(r);
    window.scrollTo(0, 0);
  }

  if (!ready) {
    return (
      <div className="main">
        <div className="note">読み込み中…</div>
      </div>
    );
  }

  const watchCount = candidates.filter((c) => c.watch).length;

  return (
    <>
      <header className="app-header">
        <h1>
          着地利益ツール
          <span className="fx">
            1USD = {settings.rates.fx_jpy_per_usd}円 / {candidates.length}件
          </span>
        </h1>
      </header>

      <nav className="tabbar" aria-label="メインナビゲーション">
        {TABS.map((t) => (
          <button
            key={t.name}
            aria-current={route.name === t.name || (route.name === 'detail' && t.name === 'dashboard') ? 'page' : undefined}
            onClick={() => go({ name: t.name } as Route)}
          >
            <span className="ico">{t.icon}</span>
            <span>
              {t.label}
              {t.name === 'watch' && watchCount > 0 ? ` (${watchCount})` : ''}
            </span>
          </button>
        ))}
      </nav>

      <main className="main">
        {route.name === 'dashboard' ? (
          <Dashboard onOpen={(id) => go({ name: 'detail', id })} />
        ) : null}
        {route.name === 'detail' ? (
          <CandidateDetail id={route.id} onBack={() => go({ name: 'dashboard' })} />
        ) : null}
        {route.name === 'add' ? (
          <AddCandidate onCreated={(id) => go({ name: 'detail', id })} />
        ) : null}
        {route.name === 'watch' ? <Watchlist onOpen={(id) => go({ name: 'detail', id })} /> : null}
        {route.name === 'settings' ? <Settings /> : null}
      </main>

      {toastMsg ? <div className="toast">{toastMsg}</div> : null}
    </>
  );
}

export default function App() {
  return (
    <StoreProvider>
      <Shell />
    </StoreProvider>
  );
}
