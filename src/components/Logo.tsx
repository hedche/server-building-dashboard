import React, { useState } from 'react';
import { Shield } from 'lucide-react';

interface LogoProps {
  size?: 'sm' | 'md';
  className?: string;
}

const Logo: React.FC<LogoProps> = ({ size = 'md', className = '' }) => {
  const [imageError, setImageError] = useState(false);

  // Logo customization via environment variables
  const LOGO_PATH = import.meta.env.VITE_LOGIN_LOGO_PATH?.trim();
  const LOGO_BG_COLOR = import.meta.env.VITE_LOGIN_LOGO_BG_COLOR || 'bg-green-600';

  // Size configuration
  const sizeClasses = {
    sm: 'w-10 h-10',      // 40px
    md: 'w-20 h-20',      // 80px
  };

  const iconSizes = {
    sm: 20,  // lucide-react size prop
    md: 40,
  };

  const handleImageError = () => {
    console.error('Failed to load custom logo from public directory:', LOGO_PATH);
    setImageError(true);
  };

  return (
    <div
      className={`${sizeClasses[size]} ${LOGO_BG_COLOR} rounded-full flex items-center justify-center overflow-hidden flex-shrink-0 ${className}`}
    >
      {LOGO_PATH && !imageError ? (
        <img
          src={`/${LOGO_PATH}`}
          alt="Logo"
          onError={handleImageError}
          className="w-full h-full object-cover"
          loading="eager"
        />
      ) : (
        <Shield size={iconSizes[size]} className="text-white" />
      )}
    </div>
  );
};

export default Logo;
