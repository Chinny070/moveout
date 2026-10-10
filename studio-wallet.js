export const STUDIONET_CHAIN_ID = 61999;
export const STUDIONET_CHAIN_HEX = `0x${STUDIONET_CHAIN_ID.toString(16)}`;

export function normalizeChainId(value) {
  if (typeof value === 'number') return value;
  if (typeof value !== 'string') return Number.NaN;
  return value.startsWith('0x') ? Number.parseInt(value, 16) : Number(value);
}
export async function connectWallet(provider) {
  if (!provider || typeof provider.request !== 'function') {
    throw new Error('No EIP-1193 wallet provider was found. Install or enable a compatible browser wallet.');
  }
  const accounts = await provider.request({ method: 'eth_requestAccounts' });
  if (!Array.isArray(accounts) || typeof accounts[0] !== 'string' || !/^0x[\da-f]{40}$/i.test(accounts[0])) {
    throw new Error('The wallet did not return a valid public account address.');
  }
  const chainId = normalizeChainId(await provider.request({ method: 'eth_chainId' }));
  return { address: accounts[0], chainId, correctChain: chainId === STUDIONET_CHAIN_ID };
}

export async function switchToStudioNet(provider) {
  if (!provider || typeof provider.request !== 'function') throw new Error('Wallet provider unavailable.');
  try {
    await provider.request({ method: 'wallet_switchEthereumChain', params: [{ chainId: STUDIONET_CHAIN_HEX }] });
  } catch (error) {
    if (error?.code !== 4902) throw error;
    await provider.request({
      method: 'wallet_addEthereumChain',
      params: [{ chainId: STUDIONET_CHAIN_HEX, chainName: 'GenLayer StudioNet', rpcUrls: ['https://studio.genlayer.com/api'], nativeCurrency: { name: 'GEN', symbol: 'GEN', decimals: 18 } }],
    });
  }
  const chainId = normalizeChainId(await provider.request({ method: 'eth_chainId' }));
  if (chainId !== STUDIONET_CHAIN_ID) throw new Error(`Wallet remains on chain ${chainId}; StudioNet is 61999.`);
  return chainId;
}
