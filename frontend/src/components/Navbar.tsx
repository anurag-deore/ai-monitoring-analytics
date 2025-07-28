import React from 'react';
import { Link } from 'react-router-dom';
import { UserIcon } from './icons/dashbaord.icon';
import useChatStore from './store/chatstore';
import { useModal } from './modals/useModal';

const Navbar: React.FC = () => {
  const { alerts } = useChatStore();
  const { openModal } = useModal();

  const handleQuickCreateReport = () => {
    openModal('createReport', {
      createReport: {
        onSuccess: (data, title) => {
          // You could add global notification here or redirect to reports
          console.log('Report created successfully:', { data, title });
        },
        onError: (message) => {
          // You could add global error notification here
          console.error('Failed to create report:', message);
        }
      }
    });
  };

  return (
    <nav className="bg-white border-b border-gray-200 h-16">
      <div className="flex items-center px-5 justify-between">
        <div className="flex items-center gap-3">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="24"
            height="24"
            fill="#000000"
            viewBox="0 0 256 256"
          >
            <path d="M156,16A76.2,76.2,0,0,0,84.92,64.76,53.26,53.26,0,0,0,76,64a52,52,0,0,0,0,104h37.87L97.14,195.88A8,8,0,0,0,104,208h25.87l-16.73,27.88a8,8,0,0,0,13.72,8.24l24-40A8,8,0,0,0,144,192H118.13l14.4-24H156a76,76,0,0,0,0-152Zm0,136H76a36,36,0,0,1,0-72,38.11,38.11,0,0,1,4.78.31q-.56,3.57-.77,7.23a8,8,0,0,0,16,.92A60.06,60.06,0,1,1,156,152Z"></path>
          </svg>
          <span className="text-xl">DashyAI</span>
        </div>
        <div className="flex items-center">
          <Link
            to="/alerts"
            className="relative w-6 h-6 bg-primary-500 text-gray-700 rounded-full flex items-center justify-center"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="100%"
              height="100%"
              fill="currentColor"
              viewBox="0 0 256 256"
            >
              <path d="M221.8,175.94C216.25,166.38,208,139.33,208,104a80,80,0,1,0-160,0c0,35.34-8.26,62.38-13.81,71.94A16,16,0,0,0,48,200H88.81a40,40,0,0,0,78.38,0H208a16,16,0,0,0,13.8-24.06ZM128,216a24,24,0,0,1-22.62-16h45.24A24,24,0,0,1,128,216ZM48,184c7.7-13.24,16-43.92,16-80a64,64,0,1,1,128,0c0,36.05,8.28,66.73,16,80Z"></path>
            </svg>
            {alerts.length > 0 && (
              <span className="absolute -top-2 -right-2 bg-red-500 text-white text-xs font-bold rounded-full min-w-[18px] h-[18px] flex items-center justify-center px-1">
                {alerts.length > 99 ? '99+' : alerts.length}
              </span>
            )}
          </Link>

          {/* Quick Create Report Button */}
          <button
            onClick={handleQuickCreateReport}
            className="text-sm bg-purple-100 text-purple-700 px-3 py-2 rounded-lg hover:bg-purple-200 transition-colors duration-200 flex items-center gap-2"
            title="Quick Create Report"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            <span className="hidden sm:inline">Quick Report</span>
          </button>

          <div className="flex items-center text-gray-700 px-4 py-4 border-t border-gray-200">
            <div className="w-7 h-7 bg-primary-500 rounded-full flex items-center justify-center">
              <UserIcon />
            </div>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
