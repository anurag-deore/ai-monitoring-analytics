import { useContext } from 'react';
import ModalContext from './ModalContext';

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

export const useModal = (): ModalContextType => {
  const context = useContext(ModalContext);
  if (!context) {
    throw new Error('useModal must be used within a ModalProvider');
  }
  return context;
}; 