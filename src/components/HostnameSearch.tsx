import React, { useState, useEffect, useMemo } from 'react';
import { Search, Server } from 'lucide-react';

interface HostnameSearchProps {
  hostnames: string[];
  onHostnameSelect?: (hostname: string) => void;
}

const HostnameSearch: React.FC<HostnameSearchProps> = ({ hostnames, onHostnameSelect }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [debouncedSearchTerm, setDebouncedSearchTerm] = useState('');
  const [showResults, setShowResults] = useState(false);
  const [highlightedIndex, setHighlightedIndex] = useState(-1);

  // Debounce the search term
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearchTerm(searchTerm);
    }, 300);

    return () => clearTimeout(timer);
  }, [searchTerm]);

  // Filter hostnames based on debounced search term
  const filteredHostnames = useMemo(() => {
    if (!debouncedSearchTerm.trim()) return [];
    
    const searchLower = debouncedSearchTerm.toLowerCase();
    
    // Find matches that include the search term
    const matches = hostnames.filter(hostname => 
      hostname.toLowerCase().includes(searchLower)
    );
    
    // Sort by relevance: exact matches first, then starts with, then contains
    const sorted = matches.sort((a, b) => {
      const aLower = a.toLowerCase();
      const bLower = b.toLowerCase();
      
      // Exact match
      if (aLower === searchLower) return -1;
      if (bLower === searchLower) return 1;
      
      // Starts with
      const aStartsWith = aLower.startsWith(searchLower);
      const bStartsWith = bLower.startsWith(searchLower);
      if (aStartsWith && !bStartsWith) return -1;
      if (bStartsWith && !aStartsWith) return 1;
      
      // Alphabetical for same relevance
      return aLower.localeCompare(bLower);
    });
    
    // Return top 5 matches
    return sorted.slice(0, 5);
  }, [hostnames, debouncedSearchTerm]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setSearchTerm(value);
    setShowResults(value.trim().length > 0);
    setHighlightedIndex(-1);
  };

  const handleHostnameClick = (hostname: string) => {
    setSearchTerm(hostname);
    setShowResults(false);
    setHighlightedIndex(-1);
    onHostnameSelect?.(hostname);
  };

  const handleInputFocus = () => {
    if (searchTerm.trim().length > 0) {
      setShowResults(true);
    }
  };

  const handleInputBlur = () => {
    setTimeout(() => setShowResults(false), 200);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (!showResults || filteredHostnames.length === 0) return;

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setHighlightedIndex(prev =>
          prev < filteredHostnames.length - 1 ? prev + 1 : prev
        );
        break;
      case 'ArrowUp':
        e.preventDefault();
        setHighlightedIndex(prev => (prev > 0 ? prev - 1 : -1));
        break;
      case 'Enter':
        e.preventDefault();
        if (highlightedIndex >= 0) {
          handleHostnameClick(filteredHostnames[highlightedIndex]);
        }
        break;
      case 'Escape':
        e.preventDefault();
        setShowResults(false);
        setHighlightedIndex(-1);
        break;
      default:
        break;
    }
  };

  const highlightMatchedText = (hostname: string, searchQuery: string) => {
    if (!searchQuery) return hostname;

    const regex = new RegExp(`(${searchQuery})`, 'gi');
    const parts = hostname.split(regex);

    return parts.map((part, index) =>
      regex.test(part) ? (
        <span key={index} className="font-bold text-green-400">
          {part}
        </span>
      ) : (
        part
      )
    );
  };

  return (
    <div className="relative">
      <div className="relative">
        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
          <Search size={16} className="text-gray-400" />
        </div>
        <input
          type="text"
          value={searchTerm}
          onChange={handleInputChange}
          onFocus={handleInputFocus}
          onBlur={handleInputBlur}
          onKeyDown={handleKeyDown}
          placeholder="Hostname"
          className="w-full pl-10 pr-4 py-2 bg-gray-700 border border-gray-600 text-white rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
        />
      </div>
      
      {showResults && filteredHostnames.length > 0 && (
        <div className="absolute z-10 w-full mt-1 bg-gray-700 border border-gray-600 rounded-lg shadow-lg max-h-60 overflow-y-auto">
          {filteredHostnames.map((hostname, index) => (
            <button
              key={hostname}
              onClick={() => handleHostnameClick(hostname)}
              className={`w-full px-3 py-2 text-left transition-colors flex items-center space-x-2 text-sm font-mono ${
                index === highlightedIndex
                  ? 'bg-green-600/20 text-green-300'
                  : 'text-white hover:bg-gray-600'
              }`}
            >
              <Server size={14} className={`flex-shrink-0 ${
                index === highlightedIndex ? 'text-green-400' : 'text-gray-400'
              }`} />
              <span>{highlightMatchedText(hostname, debouncedSearchTerm)}</span>
            </button>
          ))}
        </div>
      )}
      
      {showResults && debouncedSearchTerm && filteredHostnames.length === 0 && (
        <div className="absolute z-10 w-full mt-1 bg-gray-700 border border-gray-600 rounded-lg shadow-lg">
          <div className="px-3 py-2 text-gray-400 text-sm font-mono">
            No hostnames found matching "{debouncedSearchTerm}"
          </div>
        </div>
      )}
    </div>
  );
};

export default HostnameSearch;