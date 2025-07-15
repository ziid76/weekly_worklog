// 네이버 스타일 인터랙션 스크립트

class NaverStyleUI {
    constructor() {
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.initializeComponents();
        this.setupKeyboardShortcuts();
    }

    setupEventListeners() {
        // 카드 호버 효과
        $(document).on('mouseenter', '.card', function() {
            $(this).addClass('shadow-lg').css('transform', 'translateY(-2px)');
        }).on('mouseleave', '.card', function() {
            $(this).removeClass('shadow-lg').css('transform', 'translateY(0)');
        });

        // 버튼 클릭 효과
        $(document).on('click', '.btn', function() {
            const $btn = $(this);
            $btn.addClass('btn-clicked');
            setTimeout(() => $btn.removeClass('btn-clicked'), 150);
        });

        // 테이블 행 선택
        $(document).on('click', '.table tbody tr', function() {
            $(this).addClass('table-active').siblings().removeClass('table-active');
        });

        // 검색 입력 포커스 효과
        $(document).on('focus', 'input[type="search"], input[type="text"]', function() {
            $(this).parent().addClass('input-focused');
        }).on('blur', 'input[type="search"], input[type="text"]', function() {
            $(this).parent().removeClass('input-focused');
        });

        // 폼 제출 로딩 상태
        $(document).on('submit', 'form', this.handleFormSubmit);

        // 무한 스크롤
        $(window).on('scroll', this.handleInfiniteScroll);

        // 모바일 사이드바 토글
        $(document).on('click', '.navbar-toggler', function() {
            $('#sidebar').toggleClass('show');
            $('body').toggleClass('sidebar-open');
        });

        // 사이드바 외부 클릭시 닫기
        $(document).on('click', function(e) {
            if (!$(e.target).closest('#sidebar, .navbar-toggler').length) {
                $('#sidebar').removeClass('show');
                $('body').removeClass('sidebar-open');
            }
        });
    }

    initializeComponents() {
        // 툴팁 초기화
        this.initTooltips();
        
        // 프로그레스 바 애니메이션
        this.animateProgressBars();
        
        // 숫자 카운터 애니메이션
        this.animateCounters();
        
        // 테이블 반응형 처리
        this.makeTablesResponsive();
        
        // 이미지 지연 로딩
        this.initLazyLoading();
    }

    initTooltips() {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }

    animateProgressBars() {
        $('.progress-naver .progress-bar').each(function() {
            const $bar = $(this);
            const width = $bar.data('width') || $bar.attr('aria-valuenow');
            $bar.css('width', '0%').animate({ width: width + '%' }, 1000);
        });
    }

    animateCounters() {
        $('.stat-card h4, .stat-number').each(function() {
            const $this = $(this);
            const countTo = parseInt($this.text().replace(/,/g, ''));
            
            if (!isNaN(countTo)) {
                $({ countNum: 0 }).animate({
                    countNum: countTo
                }, {
                    duration: 1500,
                    easing: 'swing',
                    step: function() {
                        $this.text(Math.floor(this.countNum).toLocaleString());
                    },
                    complete: function() {
                        $this.text(countTo.toLocaleString());
                    }
                });
            }
        });
    }

    makeTablesResponsive() {
        $('.table').each(function() {
            if (!$(this).parent().hasClass('table-responsive')) {
                $(this).wrap('<div class="table-responsive"></div>');
            }
        });
    }

    initLazyLoading() {
        if ('IntersectionObserver' in window) {
            const imageObserver = new IntersectionObserver((entries, observer) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const img = entry.target;
                        img.src = img.dataset.src;
                        img.classList.remove('lazy');
                        imageObserver.unobserve(img);
                    }
                });
            });

            document.querySelectorAll('img[data-src]').forEach(img => {
                imageObserver.observe(img);
            });
        }
    }

    handleFormSubmit(e) {
        const $form = $(e.target);
        const $submitBtn = $form.find('button[type="submit"]');
        
        if ($submitBtn.length) {
            const originalText = $submitBtn.html();
            $submitBtn.html('<span class="loading"></span> 처리중...');
            $submitBtn.prop('disabled', true);
            
            // 3초 후 원래 상태로 복원 (실제로는 서버 응답에 따라 처리)
            setTimeout(() => {
                $submitBtn.html(originalText);
                $submitBtn.prop('disabled', false);
            }, 3000);
        }
    }

    handleInfiniteScroll() {
        if ($(window).scrollTop() + $(window).height() >= $(document).height() - 100) {
            // 무한 스크롤 로직
            const $loadMore = $('.load-more');
            if ($loadMore.length && !$loadMore.hasClass('loading')) {
                $loadMore.addClass('loading');
                // AJAX 요청 로직 추가
            }
        }
    }

    setupKeyboardShortcuts() {
        $(document).on('keydown', (e) => {
            // Ctrl/Cmd + K: 검색 포커스
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                $('input[type="search"]').first().focus();
            }
            
            // Ctrl/Cmd + N: 새 항목 생성
            if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
                e.preventDefault();
                const createBtn = $('.btn-primary[href*="create"]').first();
                if (createBtn.length) {
                    window.location.href = createBtn.attr('href');
                }
            }
            
            // ESC: 모달/사이드바 닫기
            if (e.key === 'Escape') {
                $('.modal').modal('hide');
                $('#sidebar').removeClass('show');
                $('body').removeClass('sidebar-open');
            }
        });
    }

    // 유틸리티 메서드들
    showNotification(message, type = 'info', duration = 5000) {
        const alertClass = 'alert-' + type;
        const iconClass = this.getIconClass(type);
        
        const alertHtml = `
            <div class="alert ${alertClass} alert-dismissible fade show" role="alert">
                <i class="fas fa-${iconClass} me-2"></i>
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        $('.main-content').prepend(alertHtml);
        
        setTimeout(() => {
            $('.alert').first().fadeOut('slow', function() {
                $(this).remove();
            });
        }, duration);
    }

    getIconClass(type) {
        const icons = {
            'success': 'check-circle',
            'error': 'exclamation-triangle',
            'warning': 'exclamation-circle',
            'info': 'info-circle'
        };
        return icons[type] || 'info-circle';
    }

    showToast(title, message, type = 'info') {
        const toastHtml = `
            <div class="toast" role="alert" aria-live="assertive" aria-atomic="true">
                <div class="toast-header">
                    <i class="fas fa-${this.getIconClass(type)} me-2 text-${type}"></i>
                    <strong class="me-auto">${title}</strong>
                    <small class="text-muted">방금 전</small>
                    <button type="button" class="btn-close" data-bs-dismiss="toast"></button>
                </div>
                <div class="toast-body">
                    ${message}
                </div>
            </div>
        `;
        
        if (!$('.toast-container').length) {
            $('body').append('<div class="toast-container"></div>');
        }
        
        $('.toast-container').append(toastHtml);
        $('.toast').last().toast('show');
    }

    confirmAction(message, callback) {
        if (confirm(message)) {
            callback();
        }
    }

    loadingOverlay(show = true) {
        if (show) {
            if (!$('.loading-overlay').length) {
                $('body').append(`
                    <div class="loading-overlay">
                        <div class="loading-spinner"></div>
                    </div>
                `);
            }
            $('.loading-overlay').fadeIn();
        } else {
            $('.loading-overlay').fadeOut();
        }
    }

    // 검색 하이라이트
    highlightSearchTerms(container, searchTerm) {
        if (!searchTerm) return;
        
        const regex = new RegExp(`(${searchTerm})`, 'gi');
        $(container).find('*').contents().filter(function() {
            return this.nodeType === 3; // 텍스트 노드만
        }).each(function() {
            const text = this.textContent;
            if (regex.test(text)) {
                const highlightedText = text.replace(regex, '<span class="search-highlight">$1</span>');
                $(this).replaceWith(highlightedText);
            }
        });
    }

    // 드래그 앤 드롭 파일 업로드
    initDragAndDrop(selector, callback) {
        $(selector).on('dragover dragenter', function(e) {
            e.preventDefault();
            e.stopPropagation();
            $(this).addClass('drag-over');
        }).on('dragleave dragend drop', function(e) {
            e.preventDefault();
            e.stopPropagation();
            $(this).removeClass('drag-over');
        }).on('drop', function(e) {
            const files = e.originalEvent.dataTransfer.files;
            if (files.length && callback) {
                callback(files);
            }
        });
    }

    // 자동 저장 기능
    autoSave(formSelector, interval = 30000) {
        setInterval(() => {
            const $form = $(formSelector);
            if ($form.length) {
                const formData = $form.serialize();
                // AJAX로 임시 저장
                $.ajax({
                    url: $form.data('autosave-url'),
                    method: 'POST',
                    data: formData,
                    success: () => {
                        this.showToast('자동 저장', '작업 내용이 자동으로 저장되었습니다.', 'success');
                    }
                });
            }
        }, interval);
    }
}

// 전역 인스턴스 생성
window.naverUI = new NaverStyleUI();

// jQuery 플러그인으로 확장
$.fn.naverCard = function() {
    return this.each(function() {
        $(this).addClass('card').hover(
            function() { $(this).addClass('shadow-lg'); },
            function() { $(this).removeClass('shadow-lg'); }
        );
    });
};

$.fn.naverButton = function() {
    return this.each(function() {
        $(this).addClass('btn').on('click', function() {
            $(this).addClass('btn-clicked');
            setTimeout(() => $(this).removeClass('btn-clicked'), 150);
        });
    });
};

// 페이지 로드 완료 후 초기화
$(document).ready(function() {
    // 기존 요소들에 네이버 스타일 적용
    $('.card').naverCard();
    $('.btn').naverButton();
    
    // 검색어 하이라이트
    const searchTerm = new URLSearchParams(window.location.search).get('q');
    if (searchTerm) {
        naverUI.highlightSearchTerms('.main-content', searchTerm);
    }
    
    // 드래그 앤 드롭 초기화
    if ($('.drag-area').length) {
        naverUI.initDragAndDrop('.drag-area', function(files) {
            console.log('Files dropped:', files);
        });
    }
    
    // 자동 저장 활성화 (폼이 있는 경우)
    if ($('form[data-autosave-url]').length) {
        naverUI.autoSave('form[data-autosave-url]');
    }
});

// 페이지 언로드 시 정리
$(window).on('beforeunload', function() {
    // 진행 중인 AJAX 요청 취소
    if (window.activeRequests) {
        window.activeRequests.forEach(request => request.abort());
    }
});
