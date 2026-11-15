import { useEffect, useState, useSyncExternalStore } from 'react';
import { createAccountController } from './privateAccount.js';

export function useAccount() {
  const [controller] = useState(() => createAccountController());
  const account = useSyncExternalStore(controller.subscribe, controller.getSnapshot);
  useEffect(() => {
    const refresh = () => { if (document.visibilityState !== 'hidden') controller.refresh(); };
    refresh();
    window.addEventListener('focus', refresh);
    window.addEventListener('pageshow', refresh);
    document.addEventListener('visibilitychange', refresh);
    return () => {
      controller.cancel();
      window.removeEventListener('focus', refresh);
      window.removeEventListener('pageshow', refresh);
      document.removeEventListener('visibilitychange', refresh);
    };
  }, [controller]);
  return [account, controller];
}
