/* app.js: merged custom and naver interactions */

// Naver style interactions
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

        // 사이드바 외부 클릭시 닫기
        $(document).on('click', function(e) {
            if (!$(e.target).closest('#sidebar, #sidebarToggle').length) {
                $('#sidebar').removeClass('show');
                $('#sidebarOverlay').removeClass('show');
                $('body').removeClass('sidebar-open');
            }
        });
    }

    initializeComponents() {
        this.initTooltips();
        this.animateProgressBars();
        this.animateCounters();
        this.makeTablesResponsive();
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
                $({ countNum: 0 }).animate({ countNum: countTo }, {
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
            setTimeout(() => {
                $submitBtn.html(originalText);
                $submitBtn.prop('disabled', false);
            }, 3000);
        }
    }

    handleInfiniteScroll() {
        if ($(window).scrollTop() + $(window).height() >= $(document).height() - 100) {
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
                $('#sidebarOverlay').removeClass('show');
                $('body').removeClass('sidebar-open');
            }
        });
    }

    // 유틸리티 메서드
    showNotification(message, type = 'info', duration = 5000) {
        const alertClass = 'alert-' + type;
        const iconClass = this.getIconClass(type);
        const alertHtml = `
            <div class="alert ${alertClass} alert-dismissible fade show" role="alert">
                <i class="fas fa-${iconClass} me-2"></i>
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>`;
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
            </div>`;
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
                    </div>`);
            }
            $('.loading-overlay').fadeIn();
        } else {
            $('.loading-overlay').fadeOut();
        }
    }

    highlightSearchTerms(container, searchTerm) {
        if (!searchTerm) return;
        const regex = new RegExp(`(${searchTerm})`, 'gi');
        $(container).find('*').contents().filter(function() {
            return this.nodeType === 3;
        }).each(function() {
            const text = this.textContent;
            if (regex.test(text)) {
                const highlightedText = text.replace(regex, '<span class="search-highlight">$1</span>');
                $(this).replaceWith(highlightedText);
            }
        });
    }

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

    autoSave(formSelector, interval = 30000) {
        setInterval(() => {
            const $form = $(formSelector);
            if ($form.length) {
                const formData = $form.serialize();
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

// expose global instance
window.naverUI = new NaverStyleUI();

// alias for compatibility
window.showNotification = function(message, type = 'info', duration = 5000) {
    if (window.naverUI) {
        window.naverUI.showNotification(message, type, duration);
    }
};
window.confirmDelete = function(message = '정말로 삭제하시겠습니까?') {
    return confirm(message);
};

// custom interactions from former custom.js
$(document).ready(function() {
    // 사이드바 활성 메뉴 표시
    $('.sidebar .nav-link').each(function() {
        if ($(this).attr('href') === window.location.pathname) {
            $(this).addClass('active');
        }
    });

    const $sidebar = $('#sidebar');
    const $overlay = $('#sidebarOverlay');
    const $body = $('body');
    const $toggleBtn = $('#sidebarToggle');

    function setNavbarHeight() {
        const height = $('.navbar').outerHeight() || 0;
        document.documentElement.style.setProperty('--navbar-height', height + 'px');
    }
    setNavbarHeight();
    $(window).on('resize load', setNavbarHeight);

    function openSidebar() {
        const scrollTop = $(window).scrollTop();
        $body.data('scroll-position', scrollTop);
        $sidebar.addClass('show');
        $overlay.addClass('show');
        $body.addClass('sidebar-open');
        $body.css('top', -scrollTop + 'px');
        $toggleBtn.addClass('active').attr({'aria-expanded': 'true', 'aria-label': '메뉴 닫기'});
        setTimeout(() => {
            $sidebar.find('.nav-link').first().focus();
        }, 300);
    }

    function closeSidebar() {
        $sidebar.removeClass('show');
        $overlay.removeClass('show');
        $body.removeClass('sidebar-open');
        const scrollTop = $body.data('scroll-position') || 0;
        $body.css('top', '');
        $(window).scrollTop(scrollTop);
        $toggleBtn.removeClass('active').attr({'aria-expanded': 'false', 'aria-label': '메뉴 열기'});
    }

    function toggleSidebar() {
        if ($sidebar.hasClass('show')) {
            closeSidebar();
        } else {
            openSidebar();
        }
    }

    // 모바일 환경에서도 제대로 동작하도록 click과 touchend 모두 처리
    $('#sidebarToggle').on('click touchend', function(e) {
        e.preventDefault();
        e.stopPropagation();
        toggleSidebar();
    });

    // 오버레이 영역도 터치 이벤트를 지원해 자연스럽게 닫히도록 수정
    $('#sidebarOverlay').on('click touchend', function(e) {
        e.preventDefault();
        e.stopPropagation();
        closeSidebar();
    });

    $sidebar.on('click', function(e) {
        e.stopPropagation();
    });

    $(document).keyup(function(e) {
        if (e.keyCode === 27) {
            closeSidebar();
        }
    });

    $(window).resize(function() {
        if ($(window).width() >= 768) {
            closeSidebar();
        }
    });

    $('.sidebar .nav-link').on('click', function() {
        const href = $(this).attr('href');
        if (href && href !== '#' && href !== 'javascript:void(0)') {
            if ($(window).width() < 768) {
                setTimeout(closeSidebar, 100);
            }
        }
    });

    const isTouchDevice = 'ontouchstart' in window || navigator.maxTouchPoints > 0;
    if (isTouchDevice) {
        $body.addClass('touch-device');
    }

    $(window).on('load', function() {
        if ($(window).width() < 768) {
            $sidebar.removeClass('show');
            $overlay.removeClass('show');
            $body.removeClass('sidebar-open');
        }
    });

    // ensure tables are responsive
    window.naverUI.makeTablesResponsive();
});

// clean up on unload
$(window).on('beforeunload', function() {
    if (window.activeRequests) {
        window.activeRequests.forEach(request => request.abort());
    }
});
