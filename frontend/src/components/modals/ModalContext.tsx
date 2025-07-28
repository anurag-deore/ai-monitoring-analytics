import React, { createContext, useState } from 'react';
import type { ReactNode } from 'react';
import CreateReportModal from './CreateReportModal';

type ModalType = 'createReport' | null;

interface CreateReportResponse {
  id?: string;
  message?: string;
  [key: string]: unknown;
}

interface CreateReportOptions {
  onSuccess?: (data: CreateReportResponse, title: string) => void;
  onError?: (message: string) => void;
}

interface ModalOptions {
  createReport?: CreateReportOptions;
}

interface ModalContextType {
  openModal: (type: ModalType, options?: ModalOptions) => void;
  closeModal: () => void;
  isModalOpen: (type: ModalType) => boolean;
}

const ModalContext = createContext<ModalContextType | undefined>(undefined);

interface ModalProviderProps {
  children: ReactNode;
}

export const ModalProvider: React.FC<ModalProviderProps> = ({ children }) => {
  const [currentModal, setCurrentModal] = useState<ModalType>(null);
  const [modalOptions, setModalOptions] = useState<ModalOptions | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const openModal = (type: ModalType, options?: ModalOptions) => {
    setCurrentModal(type);
    setModalOptions(options || null);
  };

  const closeModal = () => {
    if (!isLoading) {
      setCurrentModal(null);
      setModalOptions(null);
    }
  };

  const isModalOpen = (type: ModalType) => currentModal === type;

  const handleCreateReport = async (title: string) => {
    setIsLoading(true);
    try {
      const response = await fetch('http://localhost:8001/report/create', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ title }),
      });

      if (response.ok) {
        const data = await response.json();
        
        // Call the onSuccess callback if provided
        const createReportOptions = modalOptions?.createReport;
        if (createReportOptions?.onSuccess) {
          createReportOptions.onSuccess(data, title);
        }
        
        closeModal();
      } else {
        const errorData = await response.json();
        
        // Call the onError callback if provided
        const createReportOptions = modalOptions?.createReport;
        if (createReportOptions?.onError) {
          createReportOptions.onError(errorData.message || 'Failed to create report. Please try again.');
        }
      }
    } catch (error) {
      console.error('Error creating report:', error);
      
      // Call the onError callback if provided
      const createReportOptions = modalOptions?.createReport;
      if (createReportOptions?.onError) {
        createReportOptions.onError('Failed to create report. Please check your connection and try again.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const contextValue: ModalContextType = {
    openModal,
    closeModal,
    isModalOpen,
  };

  return (
    <ModalContext.Provider value={contextValue}>
      {children}
      
      {/* Render modals */}
      <CreateReportModal
        isOpen={currentModal === 'createReport'}
        onClose={closeModal}
        onSubmit={handleCreateReport}
        isLoading={isLoading}
      />
    </ModalContext.Provider>
  );
};

export default ModalContext; 